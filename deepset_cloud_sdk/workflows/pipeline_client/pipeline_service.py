"""Pipeline publishing service for deepset Cloud SDK."""
# pylint: disable=unnecessary-ellipsis,import-outside-toplevel
import asyncio
from io import StringIO
from typing import Any, Protocol, runtime_checkable

import structlog
from ruamel.yaml import YAML

from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME, CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    PipelineConfig,
)

logger = structlog.get_logger(__name__)


@runtime_checkable
class PipelineProtocol(Protocol):
    """Protocol defining the required methods for a pipeline object."""

    def dumps(self) -> str:
        """Convert the pipeline to a YAML string.

        :return: YAML string representation of the pipeline
        """
        ...

    def add_component(self, name: str, instance: Any) -> None:
        """Add a component to the pipeline.

        :param name: Name of the component
        :param instance: Component instance to add
        """
        ...


def _enable_publish_to_deepset() -> None:
    """Add publish methods to the Haystack Pipeline and AsyncPipeline classes.

    This function is called by deepset_sdk.init() to set up the SDK.
    Users should not call this function directly.
    """
    try:
        from haystack import AsyncPipeline as HaystackAsyncPipeline
        from haystack import Pipeline as HaystackPipeline
    except ImportError as err:
        raise ImportError("Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed.") from err

    async def publish_to_deepset_async(self: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Publish index or pipeline to deepset AI platform asynchronously.

        An index is a special type of pipeline with the purpose to preprocess files, preparing them for
        search and store them in a document store.

        :param config: Configuration for publishing, either `IndexConfig` or `PipelineConfig`.
            If publishing an index, the config argument is expected to be of type `IndexConfig`,
            if publishing a pipeline, the config argument is expected to be of type `PipelineConfig`.
        """
        api_config = CommonConfig()  # Uses environment variables
        async with DeepsetCloudAPI.factory(api_config) as api:
            service = PipelineService(api)
            await service.publish_async(self, config)

    def publish_to_deepset(self: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Publish index or pipeline to deepset AI platform synchronously.

        An index is a special type of pipeline with the purpose to preprocess files, preparing them for
        search and store them in a document store.

        :param config: Configuration for publishing, either `IndexConfig` or `PipelineConfig`.
            If publishing an index, the config argument is expected to be of type `IndexConfig`,
            if publishing a pipeline, the config argument is expected to be of type `PipelineConfig`.


        """
        # creates a sync wrapper around the async method since the APIs are async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(publish_to_deepset_async(self, config))

    def add_method_if_not_exists(cls: type, method_name: str, method: Any, class_name: str) -> None:
        """Add a method to a class if it doesn't exist.

        :param cls: Class to add the method to
        :param method_name: Name of the method to add
        :param method: Method to add
        :param class_name: Name of the class for logging
        """
        if not hasattr(cls, method_name):
            setattr(cls, method_name, method)
            logger.debug(f"Successfully added {method_name} method to {class_name} class")
        else:
            logger.debug(f"{method_name} method already exists on {class_name} class")

    # Add methods to both Pipeline classes
    add_method_if_not_exists(HaystackPipeline, "publish_async", publish_to_deepset_async, "Pipeline")
    add_method_if_not_exists(HaystackPipeline, "publish", publish_to_deepset, "Pipeline")
    add_method_if_not_exists(HaystackAsyncPipeline, "publish_async", publish_to_deepset_async, "AsyncPipeline")
    add_method_if_not_exists(HaystackAsyncPipeline, "publish", publish_to_deepset, "AsyncPipeline")


class PipelineService:
    """Handles the publishing of Haystack pipelines and indexes to deepset Cloud."""

    def __init__(self, api: DeepsetCloudAPI) -> None:
        """Initialize the pipeline service.

        :param api: An initialized DeepsetCloudAPI instance
        """
        self._api = api
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.indent(mapping=2, sequence=2)

    @classmethod
    async def factory(cls, config: CommonConfig) -> "PipelineService":
        """Create a new instance of the pipeline service.

        :param config: CommonConfig object.
        """
        async with DeepsetCloudAPI.factory(config) as api:
            return cls(api)

    async def publish_async(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Publish a pipeline or index to deepset AI platform.

        :param pipeline: The pipeline or index to publish. Must be a Haystack Pipeline or AsyncPipeline
        :param config: Configuration for publishing, either `IndexConfig` or `PipelineConfig`.
            If publishing an index, the config argument is expected to be of type `IndexConfig`,
            if publishing a pipeline, the config argument is expected to be of type `PipelineConfig`.

        :raises TypeError: If the pipeline object isn't a Haystack Pipeline or AsyncPipeline
        :raises ValueError: If no workspace is configured
        :raises ImportError: If haystack-ai is not installed
        """
        logger.debug(f"Starting async publishing for {config.name}")

        try:
            from haystack import AsyncPipeline as HaystackAsyncPipeline
            from haystack import Pipeline as HaystackPipeline
        except ImportError as err:
            raise ImportError("Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed.") from err

        if not isinstance(pipeline, (HaystackPipeline, HaystackAsyncPipeline)):
            raise TypeError(
                "Haystack Pipeline or AsyncPipeline object expected. "
                "Make sure you have installed haystack-ai and use Pipeline or AsyncPipeline "
                "to define your pipeline or index."
            )

        if not DEFAULT_WORKSPACE_NAME:
            raise ValueError(
                "We couldn't find the workspace to publish to in your environment. "
                "Please run 'deepset-cloud login' and follow the instructions."
            )

        if isinstance(config, IndexConfig):
            logger.debug(f"Publishing index to workspace {DEFAULT_WORKSPACE_NAME}")
            await self._publish_index(pipeline, config)
        else:
            logger.debug(f"Publishing pipeline to workspace {DEFAULT_WORKSPACE_NAME}")
            await self._publish_pipeline(pipeline, config)

    async def _publish_index(self, pipeline: PipelineProtocol, config: IndexConfig) -> None:
        """Publish an index pipeline to deepset Cloud.

        :param pipeline: The Haystack pipeline to publish
        :param config: Configuration for publishing
        """
        pipeline_yaml = self._create_config_yaml(pipeline, config)
        response = await self._api.post(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            endpoint="indexes",
            json={"name": config.name, "config_yaml": pipeline_yaml},
        )
        response.raise_for_status()
        if response.status_code == 201:
            logger.debug(f"Index {config.name} successfully created")

    async def _publish_pipeline(self, pipeline: PipelineProtocol, config: PipelineConfig) -> None:
        """Publish a pipeline to deepset Cloud.

        :param pipeline: The pipeline to publish
        :param config: Configuration for publishing
        """
        logger.debug(f"Publishing pipeline {config.name}")
        pipeline_yaml = self._create_config_yaml(pipeline, config)
        response = await self._api.post(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            endpoint="pipelines",
            json={"name": config.name, "query_yaml": pipeline_yaml},
        )
        response.raise_for_status()
        if response.status_code == 201:
            logger.debug(f"Pipeline {config.name} successfully created")

    def _create_config_yaml(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> str:
        """Create the config YAML string.

        :param pipeline: The Haystack pipeline to convert to YAML
        :param config: Configuration for publishing
        :return: Complete YAML string with inputs and outputs
        """
        # Parse the pipeline YAML
        pipeline_yaml = self._yaml.load(pipeline.dumps())

        # Add inputs and outputs
        if config.inputs and (converted_inputs := self._convert_to_yaml_dict(config.inputs)):
            pipeline_yaml["inputs"] = converted_inputs
        if config.outputs and (converted_outputs := self._convert_to_yaml_dict(config.outputs)):
            pipeline_yaml["outputs"] = converted_outputs

        # Convert back to string
        string_stream = StringIO()
        self._yaml.dump(pipeline_yaml, string_stream)
        return string_stream.getvalue()

    def _convert_to_yaml_dict(self, model: Any) -> dict:
        """Convert a Pydantic model to a YAML-compatible dictionary.

        Clears empty values from the dictionary.

        :param model: Pydantic model to convert
        :return: Dictionary ready for YAML serialization
        """
        fields = model.model_dump()
        # Remove empty values
        return {k: v for k, v in fields.items() if v}
