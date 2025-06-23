"""Pipeline importing service for deepset SDK."""

# pylint: disable=unnecessary-ellipsis,import-outside-toplevel
from __future__ import annotations

from http import HTTPStatus
from io import StringIO
from typing import Any, List, Optional, Protocol, runtime_checkable

import structlog
from httpx import Response
from pydantic import BaseModel
from ruamel.yaml import YAML

from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME, CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.models import IndexConfig, PipelineConfig

logger = structlog.get_logger(__name__)


class ErrorDetail(BaseModel):
    """Represents a validation error detail with code and message."""

    code: str
    message: str


class DeepsetValidationError(Exception):
    """Raised when pipeline or index validation fails."""

    def __init__(self, message: str, errors: List[ErrorDetail], status_code: int) -> None:
        """Initialize DeepsetValidationError.

        :param message: Error message.
        :param errors: List of validation error details.
        :param code: HTTP status code from the validation response.
        """
        super().__init__(message)
        self.errors = errors
        self.status_code = status_code


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
        :raises DeepsetValidationError: If validation is enabled and the pipeline or index is invalid.
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

        pipeline_yaml = self._from_haystack_pipeline(pipeline, config)

        await self._validate_pipeline_yaml(config, pipeline_yaml)

        if isinstance(config, IndexConfig):
            logger.debug(f"Importing index into workspace {self._workspace_name}")
            await self._import_index(config, pipeline_yaml)
        else:
            logger.debug(f"Importing pipeline into workspace {self._workspace_name}")
            await self._import_pipeline(config, pipeline_yaml)

    async def _validate_pipeline_yaml(self, config: IndexConfig | PipelineConfig, pipeline_yaml: str) -> None:
        """Validate pipeline yaml and handle errors based on strict_validation setting.

        Always validates the pipeline YAML. If strict_validation is False (default),
        logs warnings and continues. If strict_validation is True, raises error.

        :param config: Import configuration.
        :param pipeline_yaml: Pipeline YAML string to validate.
        :raises DeepsetValidationError: If strict_validation is True and the pipeline YAML is invalid.
        """
        try:
            if isinstance(config, IndexConfig):
                await self._validate_index(config.name, pipeline_yaml, config)
                return
            await self._validate_pipeline(config.name, pipeline_yaml, config)
        except DeepsetValidationError as err:
            if config.strict_validation:
                # Re-raise the error to fail the import
                raise
            # Log warning and continue with import
            logger.warning("Validation issues found.")
            logger.warning("Import will continue. Set strict_validation=True to fail on validation errors.")
            for error_detail in err.errors:
                logger.warning(f"Validation error [{error_detail.code}]: {error_detail.message}")

    async def _validate_index(self, name: str, indexing_yaml: str, config: IndexConfig) -> None:
        """Validate an index configuration.

        :param name: Name of the index.
        :param indexing_yaml: YAML configuration for the index.
        :param config: Index configuration containing overwrite flag.
        :raises DeepsetValidationError: If validation fails.
        """
        logger.debug(f"Validating index {name}.")

        # exclude name if overwrite is True, else we get an error that the name is already in use
        json_payload = {"indexing_yaml": indexing_yaml}
        if not config.overwrite:
            json_payload["name"] = name

        response = await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="pipeline_validations",
            json=json_payload,
        )

        if response.status_code != HTTPStatus.NO_CONTENT:
            self._handle_validation_error(response)

        logger.debug(f"Index validation successful for {name}.")

    async def _validate_pipeline(self, name: str, query_yaml: str, config: PipelineConfig) -> None:
        """Validate a pipeline configuration.

        :param name: Name of the pipeline.
        :param query_yaml: YAML configuration for the pipeline.
        :param config: Pipeline configuration containing overwrite flag.
        :raises DeepsetValidationError: If validation fails.
        """
        logger.debug(f"Validating pipeline {name}.")

        # exclude name if overwrite is True, else we get an error that the name is already in use
        json_payload = {"query_yaml": query_yaml}
        if not config.overwrite:
            json_payload["name"] = name

        response = await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="pipeline_validations",
            json=json_payload,
        )

        if response.status_code != HTTPStatus.NO_CONTENT:
            self._handle_validation_error(response)

        logger.debug(f"Pipeline validation successful for {name}.")

    def _handle_validation_error(self, response: Response) -> None:
        """Handle validation error response by extracting errors and raising DeepsetValidationError.

        Supports multiple error response formats:
        1. "details" field with code/message objects (preferred format)
        2. "errors" field with objects containing "msg" and "type" fields
        3. "errors" field with string values (fallback)
        4. Non-JSON responses (fallback to raw text)

        :param response: HTTP response object.
        :raises DeepsetValidationError: Always raises with formatted error details.
        """
        response_json = (
            response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        )

        if "details" in response_json:
            error_details = [
                ErrorDetail(code=detail["code"], message=detail["message"]) for detail in response_json["details"]
            ]
        elif "errors" in response_json and isinstance(response_json["errors"], list):
            errors = response_json["errors"]
            if errors and isinstance(errors[0], dict) and "msg" in errors[0] and "type" in errors[0]:
                # Handle object-based errors with 'msg' and 'type' fields
                error_details = [ErrorDetail(code=error["type"], message=error["msg"]) for error in errors]
            else:
                # Handle string-based errors
                error_message = ", ".join(str(error) for error in errors)
                error_details = [ErrorDetail(code=str(response.status_code), message=error_message)]
        else:
            error_details = [ErrorDetail(code="VALIDATION_FAILED", message=response.text)]

        error_messages = []
        for error in error_details:
            error_messages.append(f"[{error.code}] {error.message}")

        raise DeepsetValidationError(
            "Validation failed: " + "; ".join(error_messages), error_details, response.status_code
        )

    async def _import_index(self, config: IndexConfig, pipeline_yaml: str) -> None:
        """Import an index into deepset AI Platform.

        :param config: Configuration for importing an index.
        :param pipeline_yaml: Pre-generated index YAML string.
        :raises HTTPStatusError: If the index import fails.
        """
        if config.overwrite:
            response = await self._overwrite_index(name=config.name, pipeline_yaml=pipeline_yaml)
        else:
            response = await self._create_index(name=config.name, pipeline_yaml=pipeline_yaml)

        response.raise_for_status()
        logger.info("Index successfully imported.")

    async def _import_pipeline(self, config: PipelineConfig, pipeline_yaml: str) -> None:
        """Import a pipeline into deepset AI Platform.

        :param config: Configuration for importing a pipeline.
        :param pipeline_yaml: Pre-generated pipeline YAML string.
        :raises HTTPStatusError: If the pipeline import fails.
        """
        if config.overwrite:
            response = await self._overwrite_pipeline(name=config.name, pipeline_yaml=pipeline_yaml)
        else:
            response = await self._create_pipeline(name=config.name, pipeline_yaml=pipeline_yaml)

        response.raise_for_status()
        logger.info("Pipeline successfully imported.")

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
        self._add_pipeline_output_type_if_set(pipeline_dict, config)

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

    def _add_pipeline_output_type_if_set(self, pipeline_dict: dict, config: IndexConfig | PipelineConfig) -> None:
        """Add pipeline_output_type to the pipeline dict if set in PipelineConfig.

        This helps the Playground in deepset AI Platform adjust its behavior to better support the pipeline's output.

        :param pipeline_dict: The pipeline dictionary to modify.
        :param config: Configuration for importing. Only adds the field if config is PipelineConfig and pipeline_output_type is set.
        """
        if isinstance(config, PipelineConfig) and config.pipeline_output_type is not None:
            pipeline_dict["pipeline_output_type"] = config.pipeline_output_type.value

    async def _overwrite_index(self, name: str, pipeline_yaml: str) -> Response:
        """Overwrite an index in deepset AI Platform.

        If the index doesn't exist, it will be created instead.

        :param name: Name of the index.
        :param pipeline_yaml: Generated index YAML string.
        """
        response = await self._api.patch(
            workspace_name=self._workspace_name,
            endpoint=f"indexes/{name}",
            json={"config_yaml": pipeline_yaml},
        )

        # If index doesn't exist (404), create it instead
        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.debug(f"Index {name} not found, creating new index.")
            response = await self._create_index(name=name, pipeline_yaml=pipeline_yaml)

        return response

    async def _create_index(self, name: str, pipeline_yaml: str) -> Response:
        """Create an index in deepset AI Platform.

        :param name: Name of the index.
        :param pipeline_yaml: Generated index YAML string.
        :return: HTTP response from the API.
        """
        return await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="indexes",
            json={"name": name, "config_yaml": pipeline_yaml},
        )

    async def _overwrite_pipeline(self, name: str, pipeline_yaml: str) -> Response:
        """Overwrite a pipeline in deepset AI Platform.

        :param name: Name of the pipeline.
        :param pipeline_yaml: Generated pipeline YAML string.
        """
        response = await self._api.put(
            workspace_name=self._workspace_name,
            endpoint=f"pipelines/{name}/yaml",
            data={"query_yaml": pipeline_yaml},
        )

        # If pipeline doesn't exist (404), create it instead
        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.debug(f"Pipeline {name} not found, creating new pipeline.")
            response = await self._create_pipeline(name=name, pipeline_yaml=pipeline_yaml)

        return response

    async def _create_pipeline(self, name: str, pipeline_yaml: str) -> Response:
        """Create a pipeline in deepset AI Platform.

        :param name: Name of the pipeline.
        :param pipeline_yaml: Generated pipeline YAML string.
        :return: HTTP response from the API.
        """
        return await self._api.post(
            workspace_name=self._workspace_name,
            endpoint="pipelines",
            json={"name": name, "query_yaml": pipeline_yaml},
        )
