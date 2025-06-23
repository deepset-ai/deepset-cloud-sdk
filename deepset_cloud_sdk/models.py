"""General data classes for deepset SDK."""

import json
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


@dataclass
class UserInfo:
    """User info data class."""

    user_id: UUID
    given_name: str
    family_name: str


class DeepsetCloudFileBase:  # pylint: disable=too-few-public-methods
    """Base class for deepset files."""

    def __init__(self, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param meta: The file's metadata
        """
        self.name = name
        self.meta = meta

    @abstractmethod
    def content(self) -> Union[str, bytes]:
        """Return content."""
        raise NotImplementedError

    def meta_as_string(self) -> str:
        """Return metadata as a string."""
        if self.meta:
            return json.dumps(self.meta)

        return json.dumps({})


class DeepsetCloudFile(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for text files in deepset AI Platform."""

    def __init__(self, text: str, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param text: The text content of the file
        :param meta: The file's metadata
        """
        super().__init__(name, meta)
        self.text = text

    def content(self) -> str:
        """
        Return the content of the file.

        :return: The text of the file.
        """
        return self.text


# Didn't want to cause breaking changes in the DeepsetCloudFile class, though it
# is technically the same as the below, the naming of the text field will be confusing
# for users that are uploading anything other than text.


class DeepsetCloudFileBytes(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for uploading files of any valid type in deepset AI Platform."""

    def __init__(self, file_bytes: bytes, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param file_bytes: The content of the file represented in bytes
        :param meta: The file's metadata
        """
        super().__init__(name, meta)
        self.file_bytes = file_bytes

    def content(self) -> bytes:
        """
        Return the content of the file in bytes.

        :return: The content of the file in bytes.
        """
        return self.file_bytes


### Models for the pipeline client


class PipelineOutputType(str, Enum):
    """Enum for pipeline output types.

    Different types help the Playground in deepset AI Platform adjust it's behavior to better support
    your pipeline's output:
    - generative: For pipelines where an LLM generates new text as a response
    - chat: For conversational pipelines
    - extractive: For pipelines that extract answers directly from documents
    - document: For pipelines that return full documents or multiple documents as results
    """

    GENERATIVE = "generative"
    CHAT = "chat"
    EXTRACTIVE = "extractive"
    DOCUMENT = "document"


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


class BaseConfig(BaseModel):
    """Base configuration model for pipeline and index imports.

    Contains common fields shared between pipeline and index configurations.

    :param name: Name of the pipeline or index to be imported.
    :param strict_validation: Whether to fail on validation errors. Defaults to False (warnings only).
    :param overwrite: Whether to overwrite existing pipelines or indexes with the same name.
        If True and the resource doesn't exist, it will be created instead. Defaults to False.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="The name of the pipeline or index to be imported", min_length=1)
    strict_validation: bool = Field(
        default=False,
        description="Whether to fail on validation errors. If False, validation warnings are logged but import continues. Defaults to False.",
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite existing pipelines or indexes with the same name. Defaults to False.",
    )


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
        min_length=1,
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


class PipelineConfig(BaseConfig):
    """Configuration required to import the pipeline into deepset AI Platform.

    :param inputs: Pipeline input configuration. Use `PipelineInputs` model to define the inputs.
    :param outputs: Pipeline output configuration. Use `PipelineOutputs` model to define the outputs.
    :param pipeline_output_type: Optional pipeline output type to help the Playground in deepset AI Platform
        adjust its behavior. If not set, the platform will auto-detect the type.
    """

    inputs: PipelineInputs = Field(
        default_factory=PipelineInputs,
        description=("Pipeline input configuration. Use `PipelineInputs` model to define the inputs."),
    )
    outputs: PipelineOutputs = Field(
        default_factory=PipelineOutputs,
        description=("Pipeline output configuration. Use `PipelineOutputs` model to define the outputs."),
    )
    pipeline_output_type: PipelineOutputType | None = Field(
        default=None,
        description=(
            "Optional pipeline output type to help the Playground in deepset AI Platform adjust its behavior. "
            "Choose from: 'generative' (LLM generates new text), 'chat' (conversational), "
            "'extractive' (extracts answers from documents), or 'document' (returns full documents). "
            "If not set, the platform will auto-detect the type."
        ),
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


class IndexConfig(BaseConfig):
    """Index configuration for importing an index to deepset AI platform.

    :param inputs: Index input configuration. Use `IndexInputs` model to define the inputs.
    :param outputs: Index output configuration. Optional. Use `IndexOutputs` model to define the outputs.
    """

    inputs: IndexInputs = Field(
        default_factory=IndexInputs,
        description=("Input configuration for the index. Use `IndexInputs` model to define the inputs."),
    )
    outputs: IndexOutputs | None = Field(
        default_factory=IndexOutputs,
        description=("Optional output configuration for the index. Use `IndexOutputs` model to define the outputs."),
    )
