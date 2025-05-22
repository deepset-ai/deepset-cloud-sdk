"""Pipeline publishing service for deepset Cloud SDK."""
from typing import Protocol, runtime_checkable, AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager

import structlog
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.config import CommonConfig, DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.workflows.pipeline_client.models import PipelineOutputs, PipelineType, PipelineInputs, PublishConfig
from deepset_cloud_sdk.workflows.user_facing_docs.pipeline_service_docs import PipelineServiceDocs

logger = structlog.get_logger(__name__)


@runtime_checkable
class PipelineProtocol(Protocol):
    """Protocol defining the required methods for a pipeline object."""

    def dumps(self) -> str:
        """Convert the pipeline to a YAML string.

        :return: YAML string representation of the pipeline
        """
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert the pipeline to a dictionary representation.

        :return: Dictionary representation of the pipeline
        """
        ...

    def add_component(self, name: str, instance: Any) -> None:
        """Add a component to the pipeline.

        :param name: Name of the component
        :param instance: Component instance to add
        """
        ...

    def connect(self, sender: str, receiver: str) -> "PipelineProtocol":
        """Connect two components in the pipeline.

        :param sender: Component name or component.connection_name that sends data
        :param receiver: Component name or component.connection_name that receives data
        :return: The pipeline instance for method chaining
        """
        ...


class PipelineService:
    """Handles the publishing of Haystack pipelines and indexes to deepset Cloud."""

    def __init__(self, api: DeepsetCloudAPI) -> None:
        """Initialize the pipeline service.

        :param api: An initialized DeepsetCloudAPI instance
        """
        self.api = api

    @classmethod
    async def factory(cls, config: CommonConfig) -> "PipelineService":
        """Create a new instance of the pipeline service.

        :param config: CommonConfig object.
        """
        async with DeepsetCloudAPI.factory(config) as api:
            return cls(api)

    def _append_section_to_yaml(self, yaml_str: str, section_name: str, fields: dict) -> str:
        """Append a section configuration to the YAML string.

        :param yaml_str: Original YAML string
        :param section_name: Name of the section to append (e.g., 'inputs' or 'outputs')
        :param fields: Dictionary of fields to append
        :return: YAML string with section appended
        """
        # Remove empty values
        fields = {k: v for k, v in fields.items() if v}
        
        if not fields:
            return yaml_str

        section_yaml = f"\n{section_name}:\n"
        for key, value in fields.items():
            if isinstance(value, list):
                section_yaml += f"  {key}:\n"
                for item in value:
                    section_yaml += f"  - {item}\n"
            else:
                section_yaml += f"  {key}: {value}\n"

        return yaml_str.rstrip() + "\n" + section_yaml

    def _append_inputs_to_yaml(self, yaml_str: str, inputs: PipelineInputs) -> str:
        """Append inputs configuration to the YAML string.

        :param yaml_str: Original YAML string
        :param inputs: Input configuration to append
        :return: YAML string with inputs appended
        """
        input_fields = inputs.model_dump()
        return self._append_section_to_yaml(yaml_str, "inputs", input_fields)

    def _append_outputs_to_yaml(self, yaml_str: str, outputs: PipelineOutputs) -> str:
        """Append outputs configuration to the YAML string.

        :param yaml_str: Original YAML string
        :param outputs: Output configuration to append
        :return: YAML string with outputs appended
        """
        output_fields = outputs.model_dump()
        return self._append_section_to_yaml(yaml_str, "outputs", output_fields)

    def _create_config_yaml(self, pipeline: PipelineProtocol, config: PublishConfig) -> str:
        """Create the config YAML string.

        :param pipeline: The Haystack pipeline to convert to YAML
        :param config: Configuration for publishing
        :return: Complete YAML string with inputs and outputs
        """
        config_yaml = pipeline.dumps()
        config_yaml = self._append_inputs_to_yaml(config_yaml, config.inputs)
        config_yaml = self._append_outputs_to_yaml(config_yaml, config.outputs)
        return config_yaml

    async def _publish_pipeline(self, pipeline: PipelineProtocol, config: PublishConfig) -> None:
        """Publish a pipeline to deepset Cloud.

        :param pipeline: The pipeline to publish
        :param config: Configuration for publishing
        """
        logger.info(f"Publishing {config.pipeline_type.value}: {config.name}")
        pipeline_yaml = self._create_config_yaml(pipeline, config)
        response = await self.api.post(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            endpoint="pipelines",
            json={
                "name": config.name,
                "query_yaml": pipeline_yaml
            }
        )
        response.raise_for_status()
        if response.status_code == 201:
            logger.info(f"{config.pipeline_type.value} {config.name} successfully created")

    async def _publish_index(self, pipeline: PipelineProtocol, config: PublishConfig) -> None:
        """Publish an index pipeline to deepset Cloud.

        :param pipeline: The Haystack pipeline to publish
        :param config: Configuration for publishing
        """
        pipeline_yaml = self._create_config_yaml(pipeline, config)
        response = await self.api.post(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            endpoint="indexes",
            json={
                "name": config.name,
                "config_yaml": pipeline_yaml
            }
        )
        response.raise_for_status()
        if response.status_code == 201:
            logger.info(f"Index {config.name} successfully created")

    async def publish(
        self, 
        pipeline: PipelineProtocol,
        config: PublishConfig
    ) -> None:
        """Publish a pipeline or indexto deepset AI platform.

        :param pipeline: The pipeline or index to publish. Must implement the PipelineProtocol
        :param config: Configuration for publishing

        :raises TypeError: If the pipeline object doesn't implement the required protocol
        :raises ValueError: If no workspace is configured
        """
        logger.info(f"Starting publish process for {config.pipeline_type.value}: {config.name}")
        
        if not isinstance(pipeline, PipelineProtocol):
            raise TypeError(PipelineServiceDocs.INVALID_PIPELINE_TYPE_ERROR)

        if not DEFAULT_WORKSPACE_NAME:
            raise ValueError(PipelineServiceDocs.WORKSPACE_REQUIRED_ERROR)

        logger.info(f"Publishing {config.pipeline_type.value} to workspace {DEFAULT_WORKSPACE_NAME}")

        if config.pipeline_type == PipelineType.INDEX:
            await self._publish_index(pipeline, config)
        else:
            await self._publish_pipeline(pipeline, config)


def enable_publish_to_deepset() -> None:
    """Add the publish method to the Haystack Pipeline and AsyncPipeline classes if not already added."""
    try:
        from haystack import Pipeline as HaystackPipeline
        from haystack import AsyncPipeline as HaystackAsyncPipeline
        
        async def publish_to_deepset(
            self: PipelineProtocol, 
            config: PublishConfig
        ) -> None:
            """Publish this pipeline to deepset AI platform.

            :param config: Configuration for publishing
            """
            api_config = CommonConfig()  # Uses environment variables
            async with DeepsetCloudAPI.factory(api_config) as api:
                service = PipelineService(api)
                await service.publish(self, config)

        # Add publish method to Pipeline if it doesn't exist
        if not hasattr(HaystackPipeline, 'publish'):
            logger.info("Adding publish method to Haystack Pipeline class")
            HaystackPipeline.publish = publish_to_deepset
            logger.info("Successfully added publish method to Haystack Pipeline class")
        else:
            logger.info("Publish method already exists on HaystackPipeline class")

        # Add publish method to AsyncPipeline if it doesn't exist
        if not hasattr(HaystackAsyncPipeline, 'publish'):
            logger.info("Adding publish method to Haystack AsyncPipeline class")
            HaystackAsyncPipeline.publish = publish_to_deepset
            logger.info("Successfully added publish method to Haystack AsyncPipeline class")
        else:
            logger.info("Publish method already exists on HaystackAsyncPipeline class")

    except ImportError:
        logger.error("Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed.")
        pass
