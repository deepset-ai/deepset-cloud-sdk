from pydantic import ValidationError
import pytest

from deepset_cloud_sdk.workflows.pipeline_client.models import (
    PipelineInputs,
    PipelineOutputs,
    PipelineType,
    PublishConfig,
)
from deepset_cloud_sdk.workflows.user_facing_docs.pipeline_service_docs import PipelineServiceDocs


class TestPipelineInputs:
    """Test suite for the PipelineInputs model."""

    def test_create_pipeline_inputs_with_defaults(self) -> None:
        """Test creating PipelineInputs with default values."""
        inputs = PipelineInputs()
        assert inputs.query == []
        assert inputs.filters == []
        assert inputs.files == []

    def test_create_pipeline_inputs_with_values(self) -> None:
        """Test creating PipelineInputs with specific values."""
        inputs = PipelineInputs(
            query=["retriever.query"], filters=["retriever.filters"], files=["file_classifier.sources"]
        )
        assert inputs.query == ["retriever.query"]
        assert inputs.filters == ["retriever.filters"]
        assert inputs.files == ["file_classifier.sources"]

    def test_pipeline_inputs_with_additional_fields(self) -> None:
        """Test that PipelineInputs allows additional fields."""
        inputs = PipelineInputs(query=["retriever.query"], additional_meta="test", custom_field=123)
        assert inputs.query == ["retriever.query"]
        assert inputs.additional_meta == "test"
        assert inputs.custom_field == 123


class TestPipelineOutputs:
    """Test suite for the PipelineOutputs model."""

    def test_create_pipeline_outputs_with_defaults(self) -> None:
        """Test creating PipelineOutputs with default values."""
        outputs = PipelineOutputs()
        assert outputs.documents is None
        assert outputs.answers is None

    def test_create_pipeline_outputs_with_values(self) -> None:
        """Test creating PipelineOutputs with specific values."""
        outputs = PipelineOutputs(documents="retriever.documents", answers="reader.answers")
        assert outputs.documents == "retriever.documents"
        assert outputs.answers == "reader.answers"

    def test_pipeline_outputs_with_additional_fields(self) -> None:
        """Test that PipelineOutputs allows additional fields."""
        outputs = PipelineOutputs(documents="retriever.documents", additional_meta="test", custom_field=123)
        assert outputs.documents == "retriever.documents"
        assert outputs.additional_meta == "test"
        assert outputs.custom_field == 123


class TestPublishConfig:
    """Test suite for the PublishConfig model."""

    def test_create_publish_config_with_minimal_values(self) -> None:
        """Test creating PublishConfig with minimal required values."""
        config = PublishConfig(
            name="test_pipeline",
            pipeline_type=PipelineType.PIPELINE,
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="retriever.documents"),
        )
        assert config.name == "test_pipeline"
        assert config.pipeline_type == PipelineType.PIPELINE
        assert config.inputs.query == ["retriever.query"]
        assert config.outputs.documents == "retriever.documents"

    def test_publish_config_with_additional_fields_in_inputs(self) -> None:
        """Test that PublishConfig allows additional fields in inputs."""
        config = PublishConfig(
            name="test_pipeline",
            pipeline_type=PipelineType.PIPELINE,
            inputs=PipelineInputs(query=["retriever.query"], additional_meta="test", custom_field=123),
            outputs=PipelineOutputs(documents="retriever.documents"),
        )
        assert config.inputs.query == ["retriever.query"]
        assert config.inputs.additional_meta == "test"
        assert config.inputs.custom_field == 123

    def test_publish_config_rejects_additional_fields(self) -> None:
        """Test that PublishConfig rejects additional fields at its level."""
        with pytest.raises(ValidationError):
            PublishConfig(
                name="test_pipeline",
                pipeline_type=PipelineType.PIPELINE,
                inputs=PipelineInputs(query=["retriever.query"]),
                outputs=PipelineOutputs(documents="retriever.documents"),
                additional_field="test",  # This should cause an error
            )

    def test_publish_index_pipeline_without_files(self) -> None:
        """Test publishing an index pipeline without files inputs."""
        with pytest.raises(ValidationError, match=".*Indexes must define components expecting files as input*"):
            PublishConfig(name="test_index", pipeline_type=PipelineType.INDEX, inputs=PipelineInputs())

    def test_publish_pipeline_without_query(self) -> None:
        """Test publishing a query pipeline without query inputs."""
        with pytest.raises(
            ValidationError, match=".*Query pipelines must define components expecting a query as input*"
        ):
            PublishConfig(name="test_pipeline", pipeline_type=PipelineType.PIPELINE, inputs=PipelineInputs())

    def test_publish_pipeline_without_outputs(self) -> None:
        """Test publishing a query pipeline without any outputs."""
        with pytest.raises(ValidationError, match=".*Query pipelines must define at least one output.*"):
            PublishConfig(
                name="test_pipeline",
                pipeline_type=PipelineType.PIPELINE,
                inputs=PipelineInputs(query=["retriever.query"]),
                outputs=PipelineOutputs(),
            )

    def test_valid_publish_configs(self) -> None:
        """Test valid PublishConfig combinations."""
        # Valid query pipeline with documents output
        config = PublishConfig(
            name="test_pipeline",
            pipeline_type=PipelineType.PIPELINE,
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="retriever.documents"),
        )
        assert config.inputs.query == ["retriever.query"]
        assert config.outputs.documents == "retriever.documents"

        # Valid query pipeline with answers output
        config = PublishConfig(
            name="test_pipeline",
            pipeline_type=PipelineType.PIPELINE,
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(answers="reader.answers"),
        )
        assert config.outputs.answers == "reader.answers"

        # Valid query pipeline with both outputs
        config = PublishConfig(
            name="test_pipeline",
            pipeline_type=PipelineType.PIPELINE,
            inputs=PipelineInputs(query=["retriever.query"], filters=["retriever.filters"]),
            outputs=PipelineOutputs(documents="retriever.documents", answers="reader.answers"),
        )
        assert config.inputs.filters == ["retriever.filters"]
        assert config.outputs.documents == "retriever.documents"
        assert config.outputs.answers == "reader.answers"

        # Valid index pipeline without outputs
        config = PublishConfig(
            name="test_index",
            pipeline_type=PipelineType.INDEX,
            inputs=PipelineInputs(files=["file_classifier.sources"]),
        )
        assert config.inputs.files == ["file_classifier.sources"]

        # Valid index pipeline with optional outputs
        config = PublishConfig(
            name="test_index",
            pipeline_type=PipelineType.INDEX,
            inputs=PipelineInputs(files=["file_classifier.sources"]),
            outputs=PipelineOutputs(documents="retriever.documents"),
        )
        assert config.inputs.files == ["file_classifier.sources"]
        assert config.outputs.documents == "retriever.documents"

    def test_publish_config_with_invalid_name(self) -> None:
        """Test creating PublishConfig with invalid name."""
        with pytest.raises(ValidationError):
            PublishConfig(
                name="",  # Empty name is invalid
                pipeline_type=PipelineType.PIPELINE,
                inputs=PipelineInputs(query=["retriever.query"]),
                outputs=PipelineOutputs(documents="retriever.documents"),
            )

    def test_publish_config_with_invalid_pipeline_type(self) -> None:
        """Test creating PublishConfig with invalid pipeline type."""
        with pytest.raises(ValidationError):
            PublishConfig(
                name="test_pipeline",
                pipeline_type="invalid_type",  # type: ignore
                inputs=PipelineInputs(query=["retriever.query"]),
                outputs=PipelineOutputs(documents="retriever.documents"),
            )
