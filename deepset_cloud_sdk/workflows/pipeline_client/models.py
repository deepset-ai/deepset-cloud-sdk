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

        :return: Dictionary ready for YAML serialization.
        """
        fields = self.model_dump(exclude_none=True)
        # Remove empty values
        return {k: v for k, v in fields.items() if v}


class PipelineInputs(InputOutputBaseModel):
    """Pipeline input configuration.

    Defines the components that should receive the Query input and any filters that apply to it.

    :param query: List of components that will receive the `query` input.
        Specify each component in the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.query'
    :param filters: Optional list of components that will receive the filters input.
        Specify each component using the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.filters'.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    query: List[str] = Field(
        ...,
        description=(
            "List of components and parameters that will receive the `query` input when they are executed. "
            "Use the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.query'."
        ),
        min_items=1,
    )
    filters: List[str] = Field(
        default_factory=list,
        description=(
            "List of components and parameters that will receive the `filters` input when they are executed. "
            "Use the format: '<component-name>.<run-method-parameter-name>', for example: 'retriever.filters'."
        ),
    )


class PipelineOutputs(InputOutputBaseModel):
    """Pipeline output configuration.

    Specify the components that will output `documents`, `answers`, or both.
    You must include at least one. The outputs of these components become the final output of the pipeline.

    :param documents: Name of the component and parameter that will provide `documents` as output.
        Use the format '<component-name>.<output-parameter>', for example: 'retriever.documents'.
    :param answers: Name of the component and parameter that will provide `answers` as output.
        Use the format '<component-name>.<output-parameter>', for example: 'reader.answers'.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in outputs

    documents: str | None = Field(
        default=None,
        description="Name of the component that will provide `documents` as output. "
        "Format: '<component-name>.<output-parameter>', for example: 'meta_ranker.documents'",
    )
    answers: str | None = Field(
        default=None,
        description="Name of the component that will provide `answers` as output. "
        "Format: '<component-name>.<output-parameter>', for example: 'answers_builder.answers'",
    )

    @model_validator(mode="after")
    def validate_documents_xor_answers(self) -> "PipelineOutputs":
        """Validate that either `documents`, `answers`, or both are defined."""
        if not self.documents and not self.answers:
            raise ValueError("Define at least one pipeline output, either 'documents, 'answers' or both.")
        return self


class IndexOutputs(InputOutputBaseModel):
    """Output configuration for the index.

    Index outputs are optional.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in outputs


class PipelineConfig(BaseModel):
    """Configuration required to import the pipeline into deepset AI Platform.

    :param name: Name of the pipeline to be imported
    :param inputs: Pipeline input configuration. Use `PipelineInputs` model to define the inputs.
    :param outputs: Pipeline output configuration. Use `PipelineOutputs` model to define the outputs.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="The name of the pipeline to be imported", min_length=1)
    inputs: PipelineInputs = Field(
        default_factory=PipelineInputs,
        description=("Pipeline input configuration. Use `PipelineInputs` model to define the inputs."),
    )
    outputs: PipelineOutputs = Field(
        default_factory=PipelineOutputs,
        description=("Pipeline output configuration. Use `PipelineOutputs` model to define the outputs."),
    )


class IndexInputs(InputOutputBaseModel):
    """Configuration required to import an index into deepset AI Platform.

    Defines the index components that should receive the `Files` input.

    :param files: List of components and parameters that should receive files as input.
        Specify the components using the format: '<component-name>.<run-method-parameter-name>', for example: 'file_type_router.sources'.
    """

    model_config = {"extra": "allow"}  # Allow additional fields in inputs

    files: List[str] = Field(
        default_factory=list,
        description=(
            "List of components and parameters that will receive files as input when they're executed. "
            "Format: '<component-name>.<run-parameter-name>', for example: 'file_type_router.sources'."
        ),
    )


class IndexConfig(BaseModel):
    """Index configuration for importing an index to deepset AI platform.

    :param name: Name of the index to be imported.
    :param inputs: Index input configuration. Use `IndexInputs` model to define the inputs.
    :param outputs: Index output configuration. Optional. Use `IndexOutputs` model to define the outputs.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Name of the index to be imported.", min_length=1)
    inputs: IndexInputs = Field(
        default_factory=IndexInputs,
        description=("Input configuration for the index. Use `IndexInputs` model to define the inputs."),
    )
    outputs: IndexOutputs | None = Field(
        default_factory=IndexOutputs,
        description=("Optional output configuration for the index. Use `IndexOutputs` model to define the outputs."),
    )
