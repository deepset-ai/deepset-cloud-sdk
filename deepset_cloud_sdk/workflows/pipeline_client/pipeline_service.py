"""Pipeline importing service for deepset Cloud SDK."""
# pylint: disable=unnecessary-ellipsis,import-outside-toplevel
from __future__ import annotations

import asyncio
from http import HTTPStatus
from io import StringIO
from typing import Any, Optional, Protocol, runtime_checkable

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
    """Protocol defining the required methods for a Haystack Pipeline or AsyncPipeline."""

    def dumps(self) -> str:
        """Convert the pipeline to a YAML string.

        :return: YAML string representation of the pipeline.
        """
        ...

    def add_component(self, name: str, instance: Any) -> None:
        """Add a component to the pipeline.

        :param name: Name of the component.
        :param instance: Component instance to add.
        """
        ...


def _enable_import_into_deepset(api_config: CommonConfig, workspace_name: str) -> None:
    """Add import methods to the Haystack Pipeline and AsyncPipeline classes.

    This function is called by deepset_sdk.init() to set up the SDK.
    Users should not call this function directly.

    :param api_config: CommonConfig instance to use for API configuration.
    :param workspace_name: Workspace name to use.
    """
    try:
        from haystack import AsyncPipeline as HaystackAsyncPipeline
        from haystack import Pipeline as HaystackPipeline
    except ImportError as err:
        raise ImportError(
            "Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed. Run 'pip install haystack-ai'."
        ) from err

    async def import_into_deepset_async(self: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Import an index or pipeline into deepset AI platform asynchronously.

        An index processes files and stores them in a document store, making them available for
        query pipelines to search.

        :param config: Configuration for importing, use either `IndexConfig` or `PipelineConfig`.
            If importing an index, the config argument is expected to be of type `IndexConfig`,
            if importing a pipeline, the config argument is expected to be of type `PipelineConfig`.
        """
        async with DeepsetCloudAPI.factory(api_config) as api:
            service = PipelineService(api, workspace_name)
            await service.import_async(self, config)

    def import_into_deepset(self: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Import index or pipeline into deepset AI platform synchronously.

        An index processes files and stores them in a document store, making them available for
        query pipelines to search.

        :param config: Configuration for importing into deepset, use either `IndexConfig` or `PipelineConfig`.
            If importing an index, the config argument is expected to be of type `IndexConfig`,
            if importing a pipeline, the config argument is expected to be of type `PipelineConfig`.
        """
        # creates a sync wrapper around the async method since the APIs are async
        try:
            loop = asyncio.get_event_loop()
            should_close = False
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            should_close = True

        try:
            return loop.run_until_complete(import_into_deepset_async(self, config))
        finally:
            if should_close:
                loop.close()

    def add_method_if_not_exists(cls: type, method_name: str, method: Any, class_name: str) -> None:
        """Add a method to a class if it doesn't exist.

        :param cls: Class to add the method to.
        :param method_name: Name of the method to add.
        :param method: Method to add.
        :param class_name: Name of the class for logging.
        """
        if not hasattr(cls, method_name):
            setattr(cls, method_name, method)
            logger.debug(f"Successfully added {method_name} method to {class_name} class")
        else:
            logger.debug(f"{method_name} method already exists on {class_name} class")

    # Add methods to both Pipeline classes
    add_method_if_not_exists(HaystackPipeline, "import_into_deepset_async", import_into_deepset_async, "Pipeline")
    add_method_if_not_exists(HaystackPipeline, "import_into_deepset", import_into_deepset, "Pipeline")
    add_method_if_not_exists(
        HaystackAsyncPipeline, "import_into_deepset_async", import_into_deepset_async, "AsyncPipeline"
    )
    add_method_if_not_exists(HaystackAsyncPipeline, "import_into_deepset", import_into_deepset, "AsyncPipeline")


class PipelineService:
    """Handles the importing of Haystack pipelines and indexes into deepset AI platform."""

    def __init__(self, api: DeepsetCloudAPI, workspace_name: Optional[str] = None) -> None:
        """Initialize the pipeline service.

        :param api: An initialized DeepsetCloudAPI instance.
        :param workspace_name: Optional workspace name to use instead of environment variable.
        """
        self._api = api
        self._workspace_name = workspace_name or DEFAULT_WORKSPACE_NAME
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.indent(mapping=2, sequence=2)

    @classmethod
    async def factory(cls, config: CommonConfig, workspace_name: Optional[str] = None) -> PipelineService:
        """Create a new instance of the pipeline service.

        :param config: CommonConfig object.
        :param workspace_name: Optional workspace name to use instead of environment variable.
        """
        async with DeepsetCloudAPI.factory(config) as api:
            return cls(api, workspace_name)

    async def import_async(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Import a pipeline or an index into deepset AI platform.

        :param pipeline: The pipeline or index to import. Must be a Haystack Pipeline or AsyncPipeline.
        :param config: Configuration for importing, either `IndexConfig` or `PipelineConfig`.
            If importing an index, the config argument is expected to be of type `IndexConfig`,
            if importing a pipeline, the config argument is expected to be of type `PipelineConfig`.

        :raises TypeError: If the pipeline object isn't a Haystack Pipeline or AsyncPipeline.
        :raises ValueError: If no workspace is configured.
        :raises ImportError: If haystack-ai is not installed.
        """
        logger.debug(f"Starting async importing for {config.name}")

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

        if not self._workspace_name:
            raise ValueError(
                "The workspace to import into is not configured. "
                "Run 'deepset-cloud login' and follow the instructions or configure the workspace name on the SDK instance."
            )

        if isinstance(config, IndexConfig):
            logger.debug(f"Importing index into workspace {self._workspace_name}")
            await self._import_index(pipeline, config)
        else:
            logger.debug(f"Importing pipeline into workspace {self._workspace_name}")
            await self._import_pipeline(pipeline, config)

    async def _import_index(self, pipeline: PipelineProtocol, config: IndexConfig) -> None:
        """Import an index into deepset AI Platform.

        :param pipeline: The Haystack pipeline to import.
        :param config: Configuration for importing an index.
        """
        pipeline_yaml = self._from_haystack_pipeline(pipeline, config)
        response = await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="indexes",
            json={"name": config.name, "config_yaml": pipeline_yaml},
        )
        response.raise_for_status()
        if response.status_code == HTTPStatus.NO_CONTENT:
            logger.debug(f"Index {config.name} successfully created.")

    async def _import_pipeline(self, pipeline: PipelineProtocol, config: PipelineConfig) -> None:
        """Import a pipeline into deepset AI Platform.

        :param pipeline: The Haystack pipeline to import.
        :param config: Configuration for importing a pipeline.
        """
        logger.debug(f"Importing pipeline {config.name}")
        pipeline_yaml = self._from_haystack_pipeline(pipeline, config)
        response = await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="pipelines",
            json={"name": config.name, "query_yaml": pipeline_yaml},
        )
        response.raise_for_status()
        if response.status_code == HTTPStatus.NO_CONTENT:
            logger.debug(f"Pipeline {config.name} successfully created.")

    def _from_haystack_pipeline(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> str:
        """Create a YAML configuration from the pipeline.

        :param pipeline: The Haystack pipeline to create the configuration for.
        :param config: Configuration for importing.
        :return: YAML configuration as a string.
        """
        # Parse the pipeline YAML
        pipeline_dict = self._yaml.load(pipeline.dumps())
        self._add_inputs_and_outputs(pipeline_dict, config)

        # Convert back to string
        yaml_str = StringIO()
        self._yaml.dump(pipeline_dict, yaml_str)
        return yaml_str.getvalue()

    def _add_inputs_and_outputs(self, pipeline_dict: dict, config: IndexConfig | PipelineConfig) -> None:
        """Add inputs and outputs to the pipeline dictionary from config.

        :param pipeline_dict: The pipeline dictionary to add inputs and outputs to.
        :param config: Configuration for importing.
        """
        if config.inputs and (converted_inputs := config.inputs.to_yaml_dict()):
            pipeline_dict["inputs"] = converted_inputs
        if config.outputs and (converted_outputs := config.outputs.to_yaml_dict()):
            pipeline_dict["outputs"] = converted_outputs
