"""Tests for the pipeline service."""
import builtins
import textwrap
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from haystack import AsyncPipeline, Pipeline
from haystack.components.converters import CSVToDocument, TextFileToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.routers import FileTypeRouter
from httpx import Response

from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)
from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    DeepsetValidationError,
    ErrorDetail,
    PipelineService,
)


class TestImportPipelineService:
    """Test suite for the PipelineService import functionality."""

    @pytest.fixture
    def mock_api(self) -> AsyncMock:
        """Create a mock API client."""
        mock = AsyncMock()
        mock.post.return_value = Mock(status_code=201)
        return mock

    @pytest.fixture
    def pipeline_service(self, mock_api: AsyncMock) -> PipelineService:
        """Create a pipeline service instance with a mock API client."""
        return PipelineService(mock_api, workspace_name="default")

    @pytest.fixture
    def index_pipeline(self) -> Pipeline:
        """Create a sample index pipeline."""
        file_type_router = FileTypeRouter(mime_types=["text/plain", "text/csv"])

        text_converter = TextFileToDocument(encoding="utf-8")
        csv_converter = CSVToDocument(encoding="utf-8")
        joiner = DocumentJoiner(join_mode="concatenate", sort_by_score=False)

        pipeline_index = Pipeline()

        pipeline_index.add_component("file_type_router", file_type_router)
        pipeline_index.add_component("text_converter", text_converter)
        pipeline_index.add_component("csv_converter", csv_converter)
        pipeline_index.add_component("joiner", joiner)

        pipeline_index.connect("file_type_router.text/plain", "text_converter.sources")
        pipeline_index.connect("file_type_router.text/csv", "csv_converter.sources")
        pipeline_index.connect("text_converter.documents", "joiner.documents")
        pipeline_index.connect("csv_converter.documents", "joiner.documents")

        return pipeline_index

    @pytest.fixture
    def async_index_pipeline(self) -> AsyncPipeline:
        """Create a sample async index pipeline."""
        file_type_router = FileTypeRouter(mime_types=["text/plain"])
        text_converter = TextFileToDocument(encoding="utf-8")
        joiner = DocumentJoiner(join_mode="concatenate", sort_by_score=False)

        pipeline_index = AsyncPipeline()

        pipeline_index.add_component("file_type_router", file_type_router)
        pipeline_index.add_component("text_converter", text_converter)
        pipeline_index.add_component("joiner", joiner)

        pipeline_index.connect("file_type_router.text/plain", "text_converter.sources")
        pipeline_index.connect("text_converter.documents", "joiner.documents")

        return pipeline_index

    @pytest.mark.asyncio
    async def test_import_index(
        self,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        mock_api: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test importing an index pipeline."""

        # Create Import config
        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=False,
        )

        # Import the pipeline
        await pipeline_service.import_async(index_pipeline, config)

        expected_pipeline_yaml = textwrap.dedent(
            """components:
  csv_converter:
    init_parameters:
      encoding: utf-8
      store_full_path: false
    type: haystack.components.converters.csv.CSVToDocument
  file_type_router:
    init_parameters:
      additional_mimetypes:
      mime_types:
      - text/plain
      - text/csv
    type: haystack.components.routers.file_type_router.FileTypeRouter
  joiner:
    init_parameters:
      join_mode: concatenate
      sort_by_score: false
      top_k:
      weights:
    type: haystack.components.joiners.document_joiner.DocumentJoiner
  text_converter:
    init_parameters:
      encoding: utf-8
      store_full_path: false
    type: haystack.components.converters.txt.TextFileToDocument
connection_type_validation: true
connections:
- receiver: text_converter.sources
  sender: file_type_router.text/plain
- receiver: csv_converter.sources
  sender: file_type_router.text/csv
- receiver: joiner.documents
  sender: text_converter.documents
- receiver: joiner.documents
  sender: csv_converter.documents
max_runs_per_component: 100
metadata: {}
inputs:
  files:
  - file_type_router.sources
"""
        )

        mock_api.post.assert_called_once_with(
            workspace_name="default",
            endpoint="indexes",
            json={"name": "test_index", "config_yaml": expected_pipeline_yaml},
        )

    @pytest.mark.asyncio
    async def test_import_async_index(
        self,
        pipeline_service: PipelineService,
        async_index_pipeline: AsyncPipeline,
        mock_api: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test importing an async index pipeline includes async_enabled flag."""
        config = IndexConfig(
            name="test_async_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=False,
        )

        await pipeline_service.import_async(async_index_pipeline, config)

        expected_pipeline_yaml = textwrap.dedent(
            """components:
  file_type_router:
    init_parameters:
      additional_mimetypes:
      mime_types:
      - text/plain
    type: haystack.components.routers.file_type_router.FileTypeRouter
  joiner:
    init_parameters:
      join_mode: concatenate
      sort_by_score: false
      top_k:
      weights:
    type: haystack.components.joiners.document_joiner.DocumentJoiner
  text_converter:
    init_parameters:
      encoding: utf-8
      store_full_path: false
    type: haystack.components.converters.txt.TextFileToDocument
connection_type_validation: true
connections:
- receiver: text_converter.sources
  sender: file_type_router.text/plain
- receiver: joiner.documents
  sender: text_converter.documents
max_runs_per_component: 100
metadata: {}
inputs:
  files:
  - file_type_router.sources
async_enabled: true
"""
        )

        mock_api.post.assert_called_once_with(
            workspace_name="default",
            endpoint="indexes",
            json={"name": "test_async_index", "config_yaml": expected_pipeline_yaml},
        )

    @pytest.mark.asyncio
    async def test_import_index_pipeline_with_invalid_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test importing unexpected pipeline object."""
        config = IndexConfig(
            name="test_index", inputs=IndexInputs(files=["my_component.files"]), enable_validation=False
        )

        # Create an invalid pipeline (doesn't implement PipelineProtocol)
        invalid_pipeline = object()

        with pytest.raises(TypeError, match="Haystack Pipeline or AsyncPipeline object expected.*"):
            await pipeline_service.import_async(invalid_pipeline, config)  # type: ignore

    @pytest.mark.asyncio
    async def test_import_pipeline_with_outputs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test importing a pipeline."""
        mock_api = AsyncMock()
        service = PipelineService(mock_api, workspace_name="default")
        mock_pipeline = Mock(spec=Pipeline)
        mock_pipeline.dumps.return_value = textwrap.dedent(
            """components:
  retriever:
    type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
"""
        )
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
            enable_validation=False,
        )

        await service.import_async(mock_pipeline, config)
        expected_pipeline_yaml = textwrap.dedent(
            """components:
  retriever:
    type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
inputs:
  query:
  - retriever.query
outputs:
  documents: meta_ranker.documents
  answers: answer_builder.answers
"""
        )
        mock_api.post.assert_called_once_with(
            workspace_name="default",
            endpoint="pipelines",
            json={"name": "test_pipeline", "query_yaml": expected_pipeline_yaml},
        )

    @pytest.mark.asyncio
    async def test_import_pipeline_import_error(
        self, pipeline_service: PipelineService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test importing a pipeline when haystack-ai is not installed."""
        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "haystack":
                raise ImportError("Can't import Pipeline or AsyncPipeline.")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
            enable_validation=False,
        )

        with pytest.raises(
            ImportError,
            match="Can't import Pipeline or AsyncPipeline because haystack-ai is not installed. Run 'pip install haystack-ai'.",
        ):
            await pipeline_service.import_async(Mock(), config)

    @pytest.mark.asyncio
    async def test_import_index_with_outputs_and_additional_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test importing an index with outputs and additional input parameters."""
        mock_api = AsyncMock()
        service = PipelineService(mock_api, workspace_name="my-workspace")
        mock_pipeline = Mock(spec=Pipeline)
        mock_pipeline.dumps.return_value = textwrap.dedent(
            """components:
  retriever:
    type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
"""
        )
        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(
                files=["file_classifier.sources"], custom_param="custom_value", additional_meta=["test_meta"]  # type: ignore
            ),
            outputs=IndexOutputs(
                documents="meta_ranker.documents",  # type: ignore
                custom_output="custom_output_value",  # type: ignore
                other_custom_output=["other_custom_output_value"],  # type: ignore
            ),
            enable_validation=False,
        )

        await service.import_async(mock_pipeline, config)
        expected_pipeline_yaml = textwrap.dedent(
            """components:
  retriever:
    type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
inputs:
  files:
  - file_classifier.sources
  custom_param: custom_value
  additional_meta:
  - test_meta
outputs:
  documents: meta_ranker.documents
  custom_output: custom_output_value
  other_custom_output:
  - other_custom_output_value
      """
        )

        mock_api.post.assert_called_once_with(
            workspace_name="my-workspace",
            endpoint="indexes",
            json={"name": "test_index", "config_yaml": expected_pipeline_yaml},
        )


class TestAddAsyncFlagIfNeeded:
    """Test suite for the _add_async_flag_if_needed method."""

    @pytest.fixture
    def pipeline_service(self) -> PipelineService:
        """Create a pipeline service instance with a mock API client."""
        return PipelineService(Mock(), workspace_name="default")

    def test_add_async_flag_if_needed_with_async_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test that async_enabled flag is added for AsyncPipeline."""
        mock_async_pipeline = Mock(spec=AsyncPipeline)
        pipeline_dict: dict[str, Any] = {"components": {}}

        pipeline_service._add_async_flag_if_needed(mock_async_pipeline, pipeline_dict)

        assert pipeline_dict["async_enabled"] is True

    def test_add_async_flag_if_needed_with_regular_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test that async_enabled flag is not added for regular Pipeline."""
        mock_pipeline = Mock(spec=Pipeline)
        pipeline_dict: dict[str, Any] = {"components": {}}

        pipeline_service._add_async_flag_if_needed(mock_pipeline, pipeline_dict)

        assert "async_enabled" not in pipeline_dict

    def test_add_async_flag_if_needed_with_import_error(
        self, pipeline_service: PipelineService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that helper method handles import error gracefully."""
        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "haystack":
                raise ImportError("Can't import AsyncPipeline.")
            return original_import(name, *args, **kwargs)

        mock_pipeline = Mock(spec=AsyncPipeline)
        pipeline_dict: dict[str, Any] = {"components": {}}
        monkeypatch.setattr(builtins, "__import__", mock_import)

        # does not raise
        pipeline_service._add_async_flag_if_needed(mock_pipeline, pipeline_dict)
        assert "async_enabled" not in pipeline_dict


class TestValidatePipelineYaml:
    """Test suite for the validating pipeline YAML."""

    @pytest.fixture
    def mock_api(self) -> AsyncMock:
        """Create a mock API client."""
        return AsyncMock()

    @pytest.fixture
    def pipeline_service(self, mock_api: AsyncMock) -> PipelineService:
        """Create a pipeline service instance with a mock API client."""
        return PipelineService(mock_api, workspace_name="default")

    @pytest.fixture
    def test_pipeline(self) -> Pipeline:
        """Create a sample pipeline."""
        file_type_router = FileTypeRouter(mime_types=["text/plain"])
        text_converter = TextFileToDocument(encoding="utf-8")

        pipeline = Pipeline()
        pipeline.add_component("file_type_router", file_type_router)
        pipeline.add_component("text_converter", text_converter)
        pipeline.connect("file_type_router.text/plain", "text_converter.sources")

        return pipeline

    @pytest.mark.asyncio
    async def test_import_index_with_validation_success(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with successful validation."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT
        validation_response.headers = {"content-type": "application/json"}

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=True,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Should call validation endpoint first, then import endpoint
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "indexing_yaml" in validation_call.kwargs["json"]
        assert validation_call.kwargs["json"]["name"] == "test_index"

        # Check import call
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "indexes"

    @pytest.mark.asyncio
    async def test_import_pipeline_with_validation_success(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing a pipeline with successful validation."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT
        validation_response.headers = {"content-type": "application/json"}

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK

        mock_api.post.side_effect = [validation_response, import_response]

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            enable_validation=True,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Should call validation endpoint first, then import endpoint
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "query_yaml" in validation_call.kwargs["json"]
        assert validation_call.kwargs["json"]["name"] == "test_pipeline"

        # Check import call
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "pipelines"

    @pytest.mark.asyncio
    async def test_import_index_with_validation_failure(
        self,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with validation failure."""
        # Mock validation failure response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "details": [
                {"code": "INVALID_COMPONENT", "message": "Component 'invalid_component' not found"},
                {"code": "MISSING_INPUT", "message": "Required input 'files' is missing"},
            ]
        }

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(index_pipeline, config)

        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 2
        assert error.errors[0].code == "INVALID_COMPONENT"
        assert error.errors[1].code == "MISSING_INPUT"
        assert error.status_code == HTTPStatus.BAD_REQUEST

        # Should only call validation endpoint, not import endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "pipeline_validations"

    @pytest.mark.asyncio
    async def test_import_pipeline_with_validation_failure(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing a pipeline with validation failure."""
        # Mock validation failure response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "details": [
                {"code": "INVALID_CONFIGURATION", "message": "Pipeline configuration is invalid"},
            ]
        }

        mock_api.post.return_value = validation_response

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="nonexistent.replies"),
            enable_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError contains the expected information
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 1
        assert error.errors[0].code == "INVALID_CONFIGURATION"
        assert error.status_code == HTTPStatus.BAD_REQUEST

        # Should only call validation endpoint, not import endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "pipeline_validations"

    @pytest.mark.asyncio
    async def test_import_index_skip_validation(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with validation disabled."""
        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK

        mock_api.post.return_value = import_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=False,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Should only call import endpoint, not validation endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "indexes"

    @pytest.mark.asyncio
    async def test_import_pipeline_skip_validation(
        self,
        pipeline_service: PipelineService,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing a pipeline with validation disabled."""
        # Create a simple pipeline
        from haystack.components.builders import PromptBuilder

        pipeline = Pipeline()
        pipeline.add_component("prompt_builder", PromptBuilder(template="Query: {{query}}"))

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = 204
        import_response.raise_for_status.return_value = None

        mock_api.post.return_value = import_response

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            enable_validation=False,
        )

        await pipeline_service.import_async(pipeline, config)

        # Should only call import endpoint, not validation endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "pipelines"

    @pytest.mark.asyncio
    async def test_validation_with_non_json_error_response(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test validation failure with non-JSON error response."""
        # Mock validation failure response without JSON content
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        validation_response.headers = {"content-type": "text/plain"}
        validation_response.text = "Internal server error"

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError contains fallback error information
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 1
        assert error.errors[0].code == "VALIDATION_FAILED"
        assert error.errors[0].message == "Internal server error"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_validation_with_errors_field_fallback(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test validation failure with 'errors' field fallback (e.g., 500 errors)."""
        # Mock validation failure response with 'errors' field instead of 'details'
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.FAILED_DEPENDENCY
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {"errors": ["Database connection failed", "Service unavailable"]}

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            enable_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError contains the fallback error information from 'errors' field
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 1
        assert error.errors[0].code == "424"
        assert error.errors[0].message == "Database connection failed, Service unavailable"
        assert error.status_code == HTTPStatus.FAILED_DEPENDENCY
