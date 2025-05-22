"""Models for the pipeline service."""
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from deepset_cloud_sdk.workflows.user_facing_docs.pipeline_service_docs import (
    PipelineServiceDocs,
)


class PipelineType(str, Enum):
    """Enum for pipeline types that can be published."""

    PIPELINE = "pipeline"
    INDEX = "index"


class PipelineInputs(BaseModel):
    """Input configuration for the pipeline.

    For query pipelines:
    :param query: List of component names that will receive the query input (mandatory for query pipelines).
        Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'retriever.query'
    :param filters: List of component names that will receive filters input.
        Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'retriever.filters'

    For index pipelines:
    :param files: List of component names that will receive files as input.
                 Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'file_type_router.sources'
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    query: List[str] = Field(default_factory=list, description=PipelineServiceDocs.PIPELINE_QUERY_INPUTS_DESCRIPTION)
    filters: List[str] = Field(
        default_factory=list, description=PipelineServiceDocs.PIPELINE_FILTERS_INPUTS_DESCRIPTION
    )
    files: List[str] = Field(default_factory=list, description=PipelineServiceDocs.INDEX_FILES_INPUTS_DESCRIPTION)


class PipelineOutputs(BaseModel):
    """Output configuration for the pipeline.

    For query pipelines:
    :param documents: Component name that will provide documents as output.
        Should be specified as '<component-name>.<output-parameter>', e.g., 'retriever.documents'
    :param answers: Component name that will provide answers as output.
        Should be specified as '<component-name>.<output-parameter>', e.g., 'reader.answers'
    """

    model_config = {"extra": "allow"}  # Allow additional fields in outputs

    documents: str | None = Field(
        default=None,
        description="Component name that will provide documents as output. "
        "Format: '<component-name>.<output-parameter>', e.g., 'meta_ranker.documents'",
    )
    answers: str | None = Field(
        default=None,
        description="Component name that will provide answers as output. "
        "Format: '<component-name>.<output-parameter>', e.g., 'answers_builder.answers'",
    )


class PublishConfig(BaseModel):
    """Configuration for publishing a pipeline or index to deepset AI platform.

    :param name: Name of the pipeline or index to be published
    :param pipeline_type: Type of the pipeline (pipeline or index)
    :param inputs: Input configuration for the pipeline or index
    :param outputs: Output configuration for the pipeline (mandatory for query pipelines)
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description=PipelineServiceDocs.PUBLISH_CONFIG_NAME_DESCRIPTION, min_length=1)
    pipeline_type: PipelineType = Field(..., description=PipelineServiceDocs.PUBLISH_CONFIG_PIPELINE_TYPE_DESCRIPTION)
    inputs: PipelineInputs = Field(
        default_factory=PipelineInputs, description=PipelineServiceDocs.PUBLISH_CONFIG_INPUTS_DESCRIPTION
    )
    outputs: PipelineOutputs = Field(
        default_factory=PipelineOutputs, description="Output configuration for the pipeline"
    )

    @field_validator("inputs")
    def validate_inputs(cls, v: PipelineInputs, values: ValidationInfo) -> PipelineInputs:
        """Validate inputs based on pipeline type."""
        pipeline_type = values.data.get("pipeline_type")
        if pipeline_type == PipelineType.PIPELINE:
            if not v.query:
                raise ValueError(PipelineServiceDocs.VALIDATION_ERROR_QUERY_INPUT_REQUIRED)
        elif pipeline_type == PipelineType.INDEX:
            if not v.files:
                raise ValueError(PipelineServiceDocs.VALIDATION_ERROR_FILES_INPUT_REQUIRED)
        return v

    @field_validator("outputs")
    def validate_outputs(cls, v: PipelineOutputs, values: ValidationInfo) -> PipelineOutputs:
        """Validate outputs based on pipeline type."""
        pipeline_type = values.data.get("pipeline_type")
        if pipeline_type == PipelineType.PIPELINE:
            if not v.documents and not v.answers:
                raise ValueError(PipelineServiceDocs.VALIDATION_ERROR_OUTPUTS_REQUIRED)
        return v
