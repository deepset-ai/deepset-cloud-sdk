"""Models for the pipeline service."""
from typing import List

from pydantic import BaseModel, Field, model_validator


class InputOutputBaseModel(BaseModel):
    """Base model for input and output configurations.

    This class provides common functionality for input and output models, such as YAML conversion.
    """

    def to_yaml_dict(self) -> dict:
        """Convert the model to a YAML-compatible dictionary.

        Clears empty values from the dictionary.

        :return: Dictionary ready for YAML serialization
        """
        fields = self.model_dump()
        # Remove empty values
        return {k: v for k, v in fields.items() if v}


class PipelineInputs(InputOutputBaseModel):
    """Input configuration for the pipeline.

    :param query: List of components that will receive the `query` input.
        Specify each component in the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.query'
    :param filters: Optional list of components that will receive the filters input. 
        Specify each component using the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.filters'.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    query: List[str] = Field(
        ...,
        description=(
            "List of components that will receive the `query` input when they are executed. "
            "Use the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.query'."
        ),
        min_items=1,
    )
    filters: List[str] = Field(
        default_factory=list,
        description=(
            "List of components that will receive the `filters` input when they are executed. "
            "Use the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.filters'."
        ),
    )


class PipelineOutputs(InputOutputBaseModel):
    """Pipeline output configuration. 

    Specify the components that will output `documents`, `answers`, or both. You must include at least one. The outputs of these components become the final output of the pipeline.

    :param documents: Name of the component that will provide `documents` as output. 
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


class IndexOutputs(InputOutputBaseModel):
    """Output configuration for the index.

    Index outputs are optional.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in outputs


class PipelineConfig(BaseModel):
    """Pipeline configuration for importing a pipeline to deepset AI platform.

    :param name: Name of the pipeline to be imported
    :param inputs: Input configuration for the pipeline.
    :param outputs: Output configuration for the pipeline.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Name of the pipeline to be imported", min_length=1)
    inputs: PipelineInputs = Field(default_factory=PipelineInputs, description="Input configuration for the pipeline")
    outputs: PipelineOutputs = Field(
        default_factory=PipelineOutputs, description="Output configuration for the pipeline"
    )


class IndexInputs(InputOutputBaseModel):
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
    """Index configuration for importing an index to deepset AI platform.

    :param name: Name of the index to be imported
    :param inputs: Input configuration for the index
    :param outputs: Optional output configuration for the index
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Name of the index to be imported", min_length=1)
    inputs: IndexInputs = Field(default_factory=PipelineInputs, description="Input configuration for the index.")
    outputs: IndexOutputs | None = Field(
        default_factory=IndexOutputs, description="Optional output configuration for the index."
    )
