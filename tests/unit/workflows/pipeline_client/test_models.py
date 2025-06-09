import pytest
from pydantic import ValidationError

from deepset_cloud_sdk.workflows.pipeline_client.models import (
    BaseConfig,
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)


class TestBaseConfig:
    """Test suite for the BaseConfig model."""

    def test_create_base_config_with_minimal_values(self) -> None:
        """Test creating BaseConfig with minimal required values."""
        config = BaseConfig(name="test_config")
        assert config.name == "test_config"
        assert config.enable_validation is True  # Default value

    def test_create_base_config_with_all_values(self) -> None:
        """Test creating BaseConfig with all values."""
        config = BaseConfig(name="test_config", enable_validation=False)
        assert config.name == "test_config"
        assert config.enable_validation is False

    def test_base_config_with_invalid_name(self) -> None:
        """Test creating BaseConfig with invalid name."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            BaseConfig(name="")

    def test_base_config_with_additional_fields(self) -> None:
        """Test that BaseConfig forbids additional fields."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            BaseConfig(name="test_config", extra_field="test")  # type: ignore

    def test_base_config_enable_validation_explicit_true(self) -> None:
        """Test BaseConfig with explicit enable_validation=True."""
        config = BaseConfig(name="test_config", enable_validation=True)
        assert config.enable_validation is True

    def test_base_config_enable_validation_explicit_false(self) -> None:
        """Test BaseConfig with explicit enable_validation=False."""
        config = BaseConfig(name="test_config", enable_validation=False)
        assert config.enable_validation is False

    def test_inheritance_from_base_config(self) -> None:
        """Test that IndexConfig and PipelineConfig properly inherit from BaseConfig."""
        # Test that they are instances of BaseConfig
        index_config = IndexConfig(name="test_index", inputs=IndexInputs(files=["file.txt"]))
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
        )
        
        assert isinstance(index_config, BaseConfig)
        assert isinstance(pipeline_config, BaseConfig)
        
        # Test that they inherit the common fields
        assert hasattr(index_config, 'name')
        assert hasattr(index_config, 'enable_validation')
        assert hasattr(pipeline_config, 'name')
        assert hasattr(pipeline_config, 'enable_validation')
        
        # Test that the inherited fields work correctly
        assert index_config.name == "test_index"
        assert index_config.enable_validation is True  # Default value
        assert pipeline_config.name == "test_pipeline"
        assert pipeline_config.enable_validation is True  # Default value


class TestPipelineInputs:
    """Test suite for the PipelineInputs model."""

    def test_create_pipeline_inputs_with_minimal_values(self) -> None:
        """Test creating PipelineInputs with minimal required values."""
        inputs = PipelineInputs(query=["retriever.query"])
        assert inputs.query == ["retriever.query"]
        assert inputs.filters == []

    def test_create_pipeline_inputs_with_all_values(self) -> None:
        """Test creating PipelineInputs with all values."""
        inputs = PipelineInputs(
            query=["retriever.query"], filters=["retriever.filters"], additional_key="additional_value"  # type: ignore
        )
        assert inputs.query == ["retriever.query"]
        assert inputs.filters == ["retriever.filters"]

    def test_pipeline_inputs_with_additional_fields(self) -> None:
        """Test that PipelineInputs allows additional fields."""
        inputs = PipelineInputs(query=["retriever.query"], additional_meta="test", custom_field=123)  # type: ignore
        assert inputs.query == ["retriever.query"]
        assert inputs.additional_meta == "test"  # type: ignore
        assert inputs.custom_field == 123  # type: ignore

    def test_pipeline_inputs_without_query(self) -> None:
        """Test that PipelineInputs requires query field."""
        with pytest.raises(ValidationError, match="Field required"):
            PipelineInputs()  # type: ignore

    def test_pipeline_inputs_with_empty_query(self) -> None:
        """Test that PipelineInputs requires non-empty query."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            PipelineInputs(query=[])

    def test_pipeline_inputs_to_yaml_dict(self) -> None:
        """Test that to_yaml_dict correctly transforms PipelineInputs."""
        inputs = PipelineInputs(
            query=["retriever.query"], filters=["retriever.filters"], additional_key="additional_value"  # type: ignore
        )
        yaml_dict = inputs.to_yaml_dict()
        assert yaml_dict == {
            "query": ["retriever.query"],
            "filters": ["retriever.filters"],
            "additional_key": "additional_value",
        }

    def test_pipeline_inputs_to_yaml_dict_removes_empty_values(self) -> None:
        """Test that to_yaml_dict removes empty values."""
        inputs = PipelineInputs(query=["retriever.query"], filters=[], additional_key="")  # type: ignore
        yaml_dict = inputs.to_yaml_dict()
        assert yaml_dict == {"query": ["retriever.query"]}


class TestIndexInputs:
    """Test suite for IndexInputs model."""

    def test_create_index_inputs_with_defaults(self) -> None:
        """Test creating IndexInputs with default values."""
        inputs = IndexInputs()
        assert inputs.files == []

    def test_create_index_inputs_with_values(self) -> None:
        """Test creating IndexInputs with specific values."""
        inputs = IndexInputs(files=["retriever.query"])
        assert inputs.files == ["retriever.query"]

    def test_index_inputs_with_additional_fields(self) -> None:
        """Test that PipelineInputs allows additional fields."""
        inputs = IndexInputs(files=["retriever.files"], additional_meta="test", custom_field=123)  # type: ignore
        assert inputs.files == ["retriever.files"]
        assert inputs.additional_meta == "test"  # type: ignore
        assert inputs.custom_field == 123  # type: ignore

    def test_index_inputs_to_yaml_dict(self) -> None:
        """Test that to_yaml_dict correctly transforms IndexInputs."""
        inputs = IndexInputs(files=["retriever.files"], additional_meta="test", custom_field=123)  # type: ignore
        yaml_dict = inputs.to_yaml_dict()
        assert yaml_dict == {"files": ["retriever.files"], "additional_meta": "test", "custom_field": 123}

    def test_index_inputs_to_yaml_dict_removes_empty_values(self) -> None:
        """Test that to_yaml_dict removes empty values."""
        inputs = IndexInputs(files=[], additional_meta="")  # type: ignore
        yaml_dict = inputs.to_yaml_dict()
        assert yaml_dict == {}


class TestPipelineOutputs:
    """Test suite for the PipelineOutputs model."""

    def test_create_outputs_without_documents_or_answers(self) -> None:
        """Test creating Outputs with default values."""
        with pytest.raises(
            ValidationError,
            match="Define at least one pipeline output, either 'documents, 'answers' or both.*",
        ):
            PipelineOutputs()

    def test_create_outputs_with_documents(self) -> None:
        """Test creating Outputs with documents."""
        outputs = PipelineOutputs(documents="retriever.documents")
        assert outputs.documents == "retriever.documents"
        assert outputs.answers is None

    def test_create_outputs_with_answers(self) -> None:
        """Test creating Outputs with answers."""
        outputs = PipelineOutputs(answers="reader.answers")
        assert outputs.answers == "reader.answers"
        assert outputs.documents is None

    def test_create_outputs_with_both(self) -> None:
        """Test creating Outputs with both documents and answers."""
        outputs = PipelineOutputs(documents="retriever.documents", answers="reader.answers")
        assert outputs.documents == "retriever.documents"
        assert outputs.answers == "reader.answers"

    def test_pipeline_outputs_with_additional_fields(self) -> None:
        """Test that PipelineOutputs allows additional fields."""
        outputs = PipelineOutputs(
            documents="retriever.documents", additional_meta="test", custom_field=123  # type: ignore
        )
        assert outputs.documents == "retriever.documents"
        assert outputs.additional_meta == "test"  # type: ignore
        assert outputs.custom_field == 123  # type: ignore

    def test_pipeline_outputs_to_yaml_dict(self) -> None:
        """Test that to_yaml_dict correctly transforms PipelineOutputs."""
        outputs = PipelineOutputs(
            documents="retriever.documents",
            answers="reader.answers",
            additional_meta="test",
            custom_field=123,  # type: ignore
        )
        yaml_dict = outputs.to_yaml_dict()
        assert yaml_dict == {
            "documents": "retriever.documents",
            "answers": "reader.answers",
            "additional_meta": "test",
            "custom_field": 123,
        }

    def test_pipeline_outputs_to_yaml_dict_removes_empty_values(self) -> None:
        """Test that to_yaml_dict removes empty values."""
        outputs = PipelineOutputs(documents="retriever.documents", answers=None, additional_meta="")  # type: ignore
        yaml_dict = outputs.to_yaml_dict()
        assert yaml_dict == {"documents": "retriever.documents"}


class TestIndexOutputs:
    """Test suite for the IndexOutputs model."""

    def test_create_index_outputs_with_defaults(self) -> None:
        """Test creating IndexOutputs with default values."""
        outputs = IndexOutputs()
        assert outputs.model_extra == {}

    def test_index_outputs_with_additional_fields(self) -> None:
        """Test that IndexOutputs allows additional fields."""
        outputs = IndexOutputs(additional_meta="test", custom_field=123)  # type: ignore
        assert outputs.additional_meta == "test"  # type: ignore
        assert outputs.custom_field == 123  # type: ignore

    def test_index_outputs_to_yaml_dict(self) -> None:
        """Test that to_yaml_dict correctly transforms IndexOutputs."""
        outputs = IndexOutputs(additional_meta="test", custom_field=123)  # type: ignore
        yaml_dict = outputs.to_yaml_dict()
        assert yaml_dict == {"additional_meta": "test", "custom_field": 123}

    def test_index_outputs_to_yaml_dict_removes_empty_values(self) -> None:
        """Test that to_yaml_dict removes empty values."""
        outputs = IndexOutputs(additional_meta="", custom_field=None)  # type: ignore
        yaml_dict = outputs.to_yaml_dict()
        assert yaml_dict == {}


class TestPipelineConfig:
    """Test suite for the PipelineConfig model."""

    def test_create_pipeline_config_with_minimal_values(self) -> None:
        """Test creating PipelineConfig with minimal required values."""
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="answers_builder.answers"),
        )
        assert config.name == "test_pipeline"
        assert isinstance(config.inputs, PipelineInputs)
        assert isinstance(config.outputs, PipelineOutputs)
        assert config.enable_validation is True  # Default value

    def test_create_pipeline_config_with_all_values(self) -> None:
        """Test creating PipelineConfig with all values."""
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"], filters=["retriever.filters"]),
            outputs=PipelineOutputs(documents="retriever.documents", answers="reader.answers"),
            enable_validation=False,
        )
        assert config.name == "test_pipeline"
        assert config.inputs.query == ["retriever.query"]
        assert config.outputs.documents == "retriever.documents"
        assert config.enable_validation is False

    def test_pipeline_config_with_invalid_name(self) -> None:
        """Test creating PipelineConfig with invalid name."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            PipelineConfig(
                name="",
                inputs=PipelineInputs(query=["prompt_builder.query"]),
                outputs=PipelineOutputs(answers="answers_builder.answers"),
            )

    def test_pipeline_config_with_additional_fields(self) -> None:
        """Test that PipelineConfig forbids additional fields."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            PipelineConfig(name="test_pipeline", extra_field="test", inputs=PipelineInputs(query=["prompt_builder.query"]), outputs=PipelineOutputs(answers="answers_builder.answers"))  # type: ignore

    def test_pipeline_config_enable_validation_default_value(self) -> None:
        """Test that PipelineConfig enable_validation field defaults to True."""
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="answers_builder.answers"),
        )
        assert config.enable_validation is True

    def test_pipeline_config_enable_validation_explicit_true(self) -> None:
        """Test PipelineConfig with explicit enable_validation=True."""
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="answers_builder.answers"),
            enable_validation=True,
        )
        assert config.enable_validation is True

    def test_pipeline_config_enable_validation_explicit_false(self) -> None:
        """Test PipelineConfig with explicit enable_validation=False."""
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="answers_builder.answers"),
            enable_validation=False,
        )
        assert config.enable_validation is False


class TestIndexConfig:
    """Test suite for the IndexConfig model."""

    def test_create_index_config_with_minimal_values(self) -> None:
        """Test creating IndexConfig with minimal required values."""
        config = IndexConfig(name="test_index", inputs=IndexInputs(files=["file_type_router.sources"]))
        assert config.name == "test_index"
        assert isinstance(config.inputs, IndexInputs)
        assert isinstance(config.outputs, IndexOutputs)
        assert config.enable_validation is True  # Default value

    def test_create_index_config_with_all_values(self) -> None:
        """Test creating IndexConfig with all values."""
        config = IndexConfig(
            name="test_index", 
            inputs=IndexInputs(files=["file_type_router.sources"]), 
            outputs=IndexOutputs(),
            enable_validation=False,
        )
        assert config.name == "test_index"
        assert config.inputs.files == ["file_type_router.sources"]
        assert isinstance(config.outputs, IndexOutputs)
        assert config.enable_validation is False

    def test_index_config_with_invalid_name(self) -> None:
        """Test creating IndexConfig with invalid name."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            IndexConfig(name="", inputs=IndexInputs(files=["file_type_router.sources"]))

    def test_index_config_with_additional_fields(self) -> None:
        """Test that IndexConfig forbids additional fields."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            IndexConfig(name="test_index", inputs=IndexInputs(files=["file_type_router.sources"]), extra_field="test")  # type: ignore

    def test_index_config_enable_validation_default_value(self) -> None:
        """Test that IndexConfig enable_validation field defaults to True."""
        config = IndexConfig(name="test_index", inputs=IndexInputs(files=["file_type_router.sources"]))
        assert config.enable_validation is True

    def test_index_config_enable_validation_explicit_true(self) -> None:
        """Test IndexConfig with explicit enable_validation=True."""
        config = IndexConfig(
            name="test_index", 
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=True,
        )
        assert config.enable_validation is True

    def test_index_config_enable_validation_explicit_false(self) -> None:
        """Test IndexConfig with explicit enable_validation=False."""
        config = IndexConfig(
            name="test_index", 
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=False,
        )
        assert config.enable_validation is False
