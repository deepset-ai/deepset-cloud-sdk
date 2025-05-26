"""Models for the pipeline service."""
from typing import List

from pydantic import BaseModel, Field, model_validator


class PipelineInputs(BaseModel):
    """Input configuration for the pipeline.

    :param query: List of component names that will receive the query input
        Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'retriever.query'
    :param filters: Optional list of component names that will receive filters input.
        Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'retriever.filters'
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    query: List[str] = Field(
        ...,
        description=(
            "List of component names that will receive the query input when being executed. "
            "Format: '<component-name>.<run-parameter-name>', e.g., 'retriever.query'"
        ),
        min_items=1,
    )
    filters: List[str] = Field(
        default_factory=list,
        description=(
            "List of component names that will receive filters input when being executed. "
            "Format: '<component-name>.<run-parameter-name>', e.g., 'retriever.filters'"
        ),
    )


class PipelineOutputs(BaseModel):
    """Output configuration for the pipeline.

    Must define at least one of `documents` or `answers`, or both.

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

    @model_validator(mode="after")
    def validate_documents_xor_answers(self) -> "PipelineOutputs":
        """Validate that at least one of documents or answers is defined."""
        if not self.documents and not self.answers:
            raise ValueError("At least one of 'documents' or 'answers' must be defined")
        return self


class IndexOutputs(BaseModel):
    """Output configuration for the index.
    Index outputs are not mandatory.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in outputs


class PipelineConfig(BaseModel):
    """Pipeline configuration for publishing a pipeline to deepset AI platform.

    :param name: Name of the pipeline to be published
    :param inputs: Input configuration for the pipeline.
    :param outputs: Output configuration for the pipeline.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Name of the pipeline to be published", min_length=1)
    inputs: PipelineInputs = Field(default_factory=PipelineInputs, description="Input configuration for the pipeline")
    outputs: PipelineOutputs = Field(
        default_factory=PipelineOutputs, description="Output configuration for the pipeline"
    )


class IndexInputs(BaseModel):
    """Input configuration for the pipeline index.

    :param files: List of component names that will receive files as input.
        Each component should be specified as '<component-name>.<run-parameter-name>', e.g., 'file_type_router.sources'
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    files: List[str] = Field(
        default_factory=list,
        description=(
            "List of component names that will receive files as input when being executed. "
            "Format: '<component-name>.<run-parameter-name>', e.g., 'file_type_router.sources'"
        ),
    )


class IndexConfig(BaseModel):
    """Index configuration for publishing an index to deepset AI platform.

    :param name: Name of the pipeline to be published
    :param inputs: Input configuration for the index
    :param outputs: Optional output configuration for the index
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Name of the index to be published", min_length=1)
    inputs: IndexInputs = Field(default_factory=PipelineInputs, description="Input configuration for the index.")
    outputs: IndexOutputs | None = Field(
        default_factory=IndexOutputs, description="Optional output configuration for the index."
    )
