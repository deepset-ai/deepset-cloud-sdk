"""Pipeline importing service for deepset Cloud SDK."""
# pylint: disable=unnecessary-ellipsis,import-outside-toplevel
from __future__ import annotations

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

        # import locally to avoid Haystack dependency to be installed in the SDK
        try:
            from haystack import AsyncPipeline as HaystackAsyncPipeline
            from haystack import Pipeline as HaystackPipeline
        except ImportError as err:
            raise ImportError(
                "Can't import Pipeline or AsyncPipeline because haystack-ai is not installed. Run 'pip install haystack-ai'."
            ) from err

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
        self._add_async_flag_if_needed(pipeline, pipeline_dict)

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

    def _add_async_flag_if_needed(self, pipeline: PipelineProtocol, pipeline_dict: dict) -> None:
        """Add async_enabled flag to pipeline dict if pipeline is AsyncPipeline.

        This enables running pipelines asynchronously in deepset.

        :param pipeline: The Haystack pipeline to check.
        :param pipeline_dict: The pipeline dictionary to modify.
        """
        try:
            from haystack import AsyncPipeline as HaystackAsyncPipeline

            if isinstance(pipeline, HaystackAsyncPipeline):
                pipeline_dict["async_enabled"] = True
        except ImportError:
            # If haystack-ai is not available, we can't check the type
            # This should not happen since we already checked in import_async
            pass
