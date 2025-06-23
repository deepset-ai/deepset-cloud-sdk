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
from structlog.testing import capture_logs

from deepset_cloud_sdk._service.pipeline_service import (
    DeepsetValidationError,
    PipelineService,
)
from deepset_cloud_sdk.models import (
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
    PipelineOutputType,
)


class TestImportPipelineService:
    """Test suite for the PipelineService import functionality."""

    @pytest.fixture
    def mock_api(self) -> AsyncMock:
        """Create a mock API client."""
        mock = AsyncMock()
        mock.post.return_value = Mock(status_code=HTTPStatus.CREATED.value)
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
            strict_validation=False,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, import_response]

        # Import the pipeline
        await pipeline_service.import_async(index_pipeline, config)

        expected_pipeline_yaml = textwrap.dedent(
            """
            components:
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
        ).lstrip()

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
        assert import_call.kwargs["json"] == {"name": "test_index", "config_yaml": expected_pipeline_yaml}

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
            strict_validation=False,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, import_response]

        await pipeline_service.import_async(async_index_pipeline, config)

        expected_pipeline_yaml = textwrap.dedent(
            """
            components:
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
        ).lstrip()

        # Should call validation endpoint first, then import endpoint
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "indexing_yaml" in validation_call.kwargs["json"]
        assert validation_call.kwargs["json"]["name"] == "test_async_index"

        # Check import call
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "indexes"
        assert import_call.kwargs["json"] == {"name": "test_async_index", "config_yaml": expected_pipeline_yaml}

    @pytest.mark.asyncio
    async def test_import_index_pipeline_with_invalid_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test importing unexpected pipeline object."""
        config = IndexConfig(
            name="test_index", inputs=IndexInputs(files=["my_component.files"]), strict_validation=False
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
            """
            components:
              retriever:
                type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
            """
        ).lstrip()
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
            strict_validation=False,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, import_response]

        await service.import_async(mock_pipeline, config)
        expected_pipeline_yaml = textwrap.dedent(
            """
            components:
              retriever:
                type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
            inputs:
              query:
              - retriever.query
            outputs:
              documents: meta_ranker.documents
              answers: answer_builder.answers
            """
        ).lstrip()
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
        assert import_call.kwargs["json"] == {"name": "test_pipeline", "query_yaml": expected_pipeline_yaml}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "output_type, output_type_yaml",
        [
            (PipelineOutputType.DOCUMENT, "document"),
            (PipelineOutputType.CHAT, "chat"),
            (PipelineOutputType.GENERATIVE, "generative"),
            (PipelineOutputType.EXTRACTIVE, "extractive"),
        ],
    )
    async def test_import_pipeline_with_pipeline_output_type(
        self, monkeypatch: pytest.MonkeyPatch, output_type: PipelineOutputType, output_type_yaml: str
    ) -> None:
        """Test importing a pipeline."""

        # Set up mock API and service
        mock_api = AsyncMock()
        pipeline_service = PipelineService(mock_api, workspace_name="default")

        pipeline = Pipeline()
        text_converter = TextFileToDocument(encoding="utf-8")
        pipeline.add_component("text_converter", text_converter)

        config = PipelineConfig(
            name="test_pipeline_with_output_type",
            inputs=PipelineInputs(query=["text_converter.sources"]),
            outputs=PipelineOutputs(documents="text_converter.documents"),
            pipeline_output_type=output_type,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, import_response]

        await pipeline_service.import_async(pipeline, config)

        # Verify that the import call was made with the correct YAML
        import_call = mock_api.post.call_args_list[1]
        actual_yaml = import_call.kwargs["json"]["query_yaml"]

        expected_pipeline_yaml = textwrap.dedent(
            f"""
            components:
              text_converter:
                init_parameters:
                  encoding: utf-8
                  store_full_path: false
                type: haystack.components.converters.txt.TextFileToDocument
            connection_type_validation: true
            connections: []
            max_runs_per_component: 100
            metadata: {{}}
            inputs:
              query:
              - text_converter.sources
            outputs:
              documents: text_converter.documents
            pipeline_output_type: {output_type_yaml}
            """
        ).lstrip()

        assert expected_pipeline_yaml == actual_yaml

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
            strict_validation=False,
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
            """
            components:
              retriever:
                type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
            """
        ).lstrip()
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
            strict_validation=False,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, import_response]

        await service.import_async(mock_pipeline, config)
        expected_pipeline_yaml = textwrap.dedent(
            """
            components:
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
        ).lstrip()

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
        assert import_call.kwargs["json"] == {"name": "test_index", "config_yaml": expected_pipeline_yaml}

    @pytest.mark.asyncio
    async def test_import_index_with_overwrite_true(
        self,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with overwrite=True uses PATCH endpoint."""
        config = IndexConfig(
            name="test_index_overwrite",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
            overwrite=True,
        )

        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful overwrite response
        overwrite_response = Mock(spec=Response)
        overwrite_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response]
        mock_api.patch.return_value = overwrite_response

        await pipeline_service.import_async(index_pipeline, config)

        # Should call validation endpoint, then PATCH for overwrite
        assert mock_api.post.call_count == 1
        assert mock_api.patch.call_count == 1

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # Check overwrite call
        overwrite_call = mock_api.patch.call_args_list[0]
        assert overwrite_call.kwargs["endpoint"] == "indexes/test_index_overwrite"
        assert "config_yaml" in overwrite_call.kwargs["json"]

    @pytest.mark.asyncio
    async def test_import_index_with_overwrite_fallback_to_create(
        self,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with overwrite=True that falls back to create when resource doesn't exist."""
        config = IndexConfig(
            name="test_index_fallback",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
            overwrite=True,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock 404 response for PUT (resource not found)
        not_found_response = Mock(spec=Response)
        not_found_response.status_code = HTTPStatus.NOT_FOUND.value

        # Mock successful creation response
        create_response = Mock(spec=Response)
        create_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, create_response]
        mock_api.patch.return_value = not_found_response

        await pipeline_service.import_async(index_pipeline, config)

        # Should call validation endpoint, then PATCH (which returns 404), then POST to create
        assert mock_api.post.call_count == 2
        assert mock_api.patch.call_count == 1

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "indexing_yaml" in validation_call.kwargs["json"]
        # When overwrite=True, name should be excluded from validation payload
        assert "name" not in validation_call.kwargs["json"]

        # Check PATCH attempt
        patch_call = mock_api.patch.call_args_list[0]
        assert patch_call.kwargs["endpoint"] == "indexes/test_index_fallback"
        assert "config_yaml" in patch_call.kwargs["json"]

    @pytest.mark.asyncio
    async def test_import_pipeline_with_overwrite_true(
        self, pipeline_service: PipelineService, index_pipeline: Pipeline, mock_api: AsyncMock
    ) -> None:
        """Test importing a pipeline with overwrite=True uses PUT endpoint."""
        config = PipelineConfig(
            name="test_pipeline_overwrite",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents"),
            strict_validation=False,
            overwrite=True,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful overwrite response
        overwrite_response = Mock(spec=Response)
        overwrite_response.status_code = HTTPStatus.OK.value

        mock_api.post.return_value = validation_response
        mock_api.put.return_value = overwrite_response

        await pipeline_service.import_async(index_pipeline, config)

        # Should call validation endpoint first, then overwrite endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.put.call_count == 1

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "query_yaml" in validation_call.kwargs["json"]
        # When overwrite=True, name should be excluded from validation payload
        assert "name" not in validation_call.kwargs["json"]

        # Check overwrite call
        overwrite_call = mock_api.put.call_args_list[0]
        assert overwrite_call.kwargs["endpoint"] == "pipelines/test_pipeline_overwrite/yaml"
        assert "query_yaml" in overwrite_call.kwargs["data"]

    @pytest.mark.asyncio
    async def test_import_pipeline_with_overwrite_fallback_to_create(
        self, pipeline_service: PipelineService, index_pipeline: Pipeline, mock_api: AsyncMock
    ) -> None:
        """Test importing a pipeline with overwrite=True that falls back to create when resource doesn't exist."""

        config = PipelineConfig(
            name="test_pipeline_fallback",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents"),
            strict_validation=False,
            overwrite=True,
        )

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock 404 response for PUT (resource not found)
        not_found_response = Mock(spec=Response)
        not_found_response.status_code = HTTPStatus.NOT_FOUND.value

        # Mock successful creation response
        create_response = Mock(spec=Response)
        create_response.status_code = HTTPStatus.CREATED.value

        mock_api.post.side_effect = [validation_response, create_response]
        mock_api.put.return_value = not_found_response

        await pipeline_service.import_async(index_pipeline, config)

        # Should call validation endpoint, then PUT (which returns 404), then POST to create
        assert mock_api.post.call_count == 2
        assert mock_api.put.call_count == 1

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"
        assert "query_yaml" in validation_call.kwargs["json"]
        # When overwrite=True, name should be excluded from validation payload
        assert "name" not in validation_call.kwargs["json"]

        # Check PUT attempt
        put_call = mock_api.put.call_args_list[0]
        assert put_call.kwargs["endpoint"] == "pipelines/test_pipeline_fallback/yaml"
        assert "query_yaml" in put_call.kwargs["data"]

        # Check fallback POST call
        create_call = mock_api.post.call_args_list[1]
        assert create_call.kwargs["endpoint"] == "pipelines"
        assert create_call.kwargs["json"]["name"] == "test_pipeline_fallback"
        assert "query_yaml" in create_call.kwargs["json"]


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


class TestAddPipelineOutputTypeIfSet:
    """Test suite for the _add_pipeline_output_type_if_set method."""

    @pytest.fixture
    def pipeline_service(self) -> PipelineService:
        """Create a pipeline service instance."""
        mock_api = AsyncMock()
        return PipelineService(mock_api, workspace_name="default")

    @pytest.mark.parametrize(
        "output_type,expected_value",
        [
            (PipelineOutputType.GENERATIVE, "generative"),
            (PipelineOutputType.CHAT, "chat"),
            (PipelineOutputType.EXTRACTIVE, "extractive"),
            (PipelineOutputType.DOCUMENT, "document"),
        ],
    )
    def test_add_pipeline_output_type_with_different_output_types(
        self, pipeline_service: PipelineService, output_type: PipelineOutputType, expected_value: str
    ) -> None:
        """Test adding different pipeline output types."""
        pipeline_dict = {"components": {"retriever": {"type": "SomeRetriever"}}, "connections": []}
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            pipeline_output_type=output_type,
        )

        pipeline_service._add_pipeline_output_type_if_set(pipeline_dict, config)

        assert pipeline_dict["pipeline_output_type"] == expected_value

    def test_add_pipeline_output_type_with_pipeline_config_and_no_output_type(
        self, pipeline_service: PipelineService
    ) -> None:
        """Test that pipeline_output_type is not added when not set in PipelineConfig."""
        pipeline_dict: dict[str, Any] = {"components": {}, "connections": []}
        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            pipeline_output_type=None,
        )

        pipeline_service._add_pipeline_output_type_if_set(pipeline_dict, config)

        assert "pipeline_output_type" not in pipeline_dict

    def test_add_pipeline_output_type_with_index_config(self, pipeline_service: PipelineService) -> None:
        """Test that pipeline_output_type is not added when using IndexConfig."""
        pipeline_dict: dict[str, Any] = {"components": {}, "connections": []}
        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_router.sources"]),
        )

        pipeline_service._add_pipeline_output_type_if_set(pipeline_dict, config)

        assert "pipeline_output_type" not in pipeline_dict


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
        validation_response.status_code = HTTPStatus.NO_CONTENT.value
        validation_response.headers = {"content-type": "application/json"}

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,
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
        validation_response.status_code = HTTPStatus.NO_CONTENT.value
        validation_response.headers = {"content-type": "application/json"}

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK

        mock_api.post.side_effect = [validation_response, import_response]

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            strict_validation=True,
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
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with validation failure."""
        # Mock validation failure response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST.value
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
            strict_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

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
        validation_response.status_code = HTTPStatus.BAD_REQUEST.value
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
            strict_validation=True,
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
    async def test_import_index_with_validation_warnings(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing an index with validation warnings (strict_validation=False)."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Should call validation endpoint first, then import endpoint
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # Check import call
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "indexes"

    @pytest.mark.asyncio
    async def test_import_pipeline_with_validation_warnings(
        self,
        pipeline_service: PipelineService,
        mock_api: AsyncMock,
    ) -> None:
        """Test importing a pipeline with validation warnings (strict_validation=False)."""
        # Create a simple pipeline
        from haystack.components.builders import PromptBuilder

        pipeline = Pipeline()
        pipeline.add_component("prompt_builder", PromptBuilder(template="Query: {{query}}"))

        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.NO_CONTENT.value
        import_response.raise_for_status.return_value = None

        mock_api.post.side_effect = [validation_response, import_response]

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            strict_validation=False,
        )

        await pipeline_service.import_async(pipeline, config)

        # Should call validation endpoint first, then import endpoint
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # Check import call
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "pipelines"

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
            strict_validation=True,
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
        """Test validation failure with 'errors' field fallback."""
        # Mock validation failure response with 'errors' field instead of 'details'
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.FAILED_DEPENDENCY.value
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {"errors": ["Database connection failed", "Service unavailable"]}

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError contains the fallback error information from 'errors' field
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 1
        assert error.errors[0].code == "424"
        assert error.errors[0].message == "Database connection failed, Service unavailable"
        assert error.status_code == 424

    @pytest.mark.asyncio
    async def test_validation_with_errors_object(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test validation failure with 'errors' field containing objects with 'msg' and 'type' fields."""
        # Mock validation failure response with 'errors' field containing objects
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST.value
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "errors": [
                {
                    "loc": ["body", "query_yaml"],
                    "msg": "Pipeline index with name 'Standard-Index-English-3' not found in workspace.",
                    "type": "index_validation_error",
                },
                {"loc": ["body", "name"], "msg": "Pipeline name is invalid", "type": "name_validation_error"},
            ]
        }

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError contains the error information from object-based errors
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 2
        assert error.errors[0].code == "index_validation_error"
        assert error.errors[0].message == "Pipeline index with name 'Standard-Index-English-3' not found in workspace."
        assert error.errors[1].code == "name_validation_error"
        assert error.errors[1].message == "Pipeline name is invalid"
        assert error.status_code == HTTPStatus.BAD_REQUEST.value

        # Should only call validation endpoint, not import endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "pipeline_validations"

    @pytest.mark.asyncio
    async def test_validation_with_mixed_errors_fallback_to_string(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test validation failure with 'errors' field containing mixed types (some missing required fields)."""
        # Mock validation failure response with 'errors' field containing incomplete objects
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY.value
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "errors": [
                {
                    "loc": ["body", "query_yaml"],
                    "msg": "Pipeline index not found",
                    # Missing 'type' field - should fallback to string handling
                },
                "Simple string error",
            ]
        }

        mock_api.post.return_value = validation_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,
        )

        with pytest.raises(DeepsetValidationError) as exc_info:
            await pipeline_service.import_async(test_pipeline, config)

        # Check that DeepsetValidationError falls back to string handling when objects are incomplete
        error = exc_info.value
        assert "Validation failed:" in str(error)
        assert len(error.errors) == 1
        assert error.errors[0].code == "422"  # Should use status code as string
        # Should join all errors as strings
        assert "Pipeline index not found" in error.errors[0].message
        assert "Simple string error" in error.errors[0].message
        assert error.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value

        # Should only call validation endpoint, not import endpoint
        assert mock_api.post.call_count == 1
        assert mock_api.post.call_args_list[0].kwargs["endpoint"] == "pipeline_validations"

    @pytest.mark.asyncio
    async def test_validation_errors_logged_as_warnings_by_default(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that validation errors are logged as warnings when strict_validation=False (default)."""
        # Mock validation failure response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST.value
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "details": [
                {"code": "INVALID_COMPONENT", "message": "Component 'invalid_component' not found"},
            ]
        }

        # Mock successful import response (import should continue despite validation errors)
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,  # Default behavior - warnings only
        )

        # Import should succeed despite validation errors
        with capture_logs() as cap_logs:
            await pipeline_service.import_async(test_pipeline, config)

        # Should call both validation and import endpoints
        assert mock_api.post.call_count == 2

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # Check import call (should proceed despite validation errors)
        import_call = mock_api.post.call_args_list[1]
        assert import_call.kwargs["endpoint"] == "indexes"

        # Check that validation errors were logged as warnings
        warning_logs = [log for log in cap_logs if log.get("log_level") == "warning"]
        assert len(warning_logs) >= 3  # Should have at least 3 warning messages

        # Check that the validation error details are in the warning logs
        validation_warning = next(
            (log for log in warning_logs if "Validation issues found" in log.get("event", "")), None
        )
        assert validation_warning is not None

        # Check that there's a warning about setting strict_validation=True
        strict_warning = next(
            (
                log
                for log in warning_logs
                if "Set strict_validation=True to fail on validation errors" in log.get("event", "")
            ),
            None,
        )
        assert strict_warning is not None

        # Check that individual error details are logged
        individual_error_warning = next(
            (log for log in warning_logs if "Validation error [INVALID_COMPONENT]:" in log.get("event", "")), None
        )
        assert individual_error_warning is not None
        assert "Component 'invalid_component' not found" in individual_error_warning.get("event", "")

    @pytest.mark.asyncio
    async def test_multiple_validation_errors_logged_individually(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that multiple validation errors are each logged individually when strict_validation=False."""
        # Mock validation failure response with multiple errors
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.BAD_REQUEST.value
        validation_response.headers = {"content-type": "application/json"}
        validation_response.json.return_value = {
            "details": [
                {"code": "INVALID_COMPONENT", "message": "Component 'invalid_component' not found"},
                {"code": "MISSING_INPUT", "message": "Required input 'files' is missing"},
                {"code": "INVALID_CONFIGURATION", "message": "Pipeline configuration is invalid"},
            ]
        }

        # Mock successful import response (import should continue despite validation errors)
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,  # Default behavior - warnings only
        )

        # Import should succeed despite validation errors
        with capture_logs() as cap_logs:
            await pipeline_service.import_async(test_pipeline, config)

        # Should call both validation and import endpoints
        assert mock_api.post.call_count == 2

        # Check that validation errors were logged as warnings
        warning_logs = [log for log in cap_logs if log.get("log_level") == "warning"]
        assert len(warning_logs) >= 5  # General warning + strict warning + 3 individual errors

        # Check that each individual validation error is logged
        individual_errors = [
            ("INVALID_COMPONENT", "Component 'invalid_component' not found"),
            ("MISSING_INPUT", "Required input 'files' is missing"),
            ("INVALID_CONFIGURATION", "Pipeline configuration is invalid"),
        ]

        for error_code, error_message in individual_errors:
            error_log = next(
                (log for log in warning_logs if f"Validation error [{error_code}]:" in log.get("event", "")), None
            )
            assert error_log is not None, f"Expected to find log for error code {error_code}"
            assert error_message in error_log.get("event", ""), f"Expected error message '{error_message}' in log"

    @pytest.mark.asyncio
    async def test_validate_index_excludes_name_when_overwrite_true(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that index validation excludes name from JSON payload when overwrite=True."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]
        mock_api.patch.return_value = import_response

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
            overwrite=True,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # When overwrite=True, name should be excluded from validation payload
        validation_json = validation_call.kwargs["json"]
        assert "name" not in validation_json
        assert "indexing_yaml" in validation_json

    @pytest.mark.asyncio
    async def test_validate_index_includes_name_when_overwrite_false(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that index validation includes name in JSON payload when overwrite=False."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]

        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
            overwrite=False,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # When overwrite=False, name should be included in validation payload
        validation_json = validation_call.kwargs["json"]
        assert validation_json["name"] == "test_index"
        assert "indexing_yaml" in validation_json

    @pytest.mark.asyncio
    async def test_validate_pipeline_excludes_name_when_overwrite_true(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that pipeline validation excludes name from JSON payload when overwrite=True."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]
        mock_api.put.return_value = import_response

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            strict_validation=False,
            overwrite=True,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # When overwrite=True, name should be excluded from validation payload
        validation_json = validation_call.kwargs["json"]
        assert "name" not in validation_json
        assert "query_yaml" in validation_json

    @pytest.mark.asyncio
    async def test_validate_pipeline_includes_name_when_overwrite_false(
        self,
        pipeline_service: PipelineService,
        test_pipeline: Pipeline,
        mock_api: AsyncMock,
    ) -> None:
        """Test that pipeline validation includes name in JSON payload when overwrite=False."""
        # Mock successful validation response
        validation_response = Mock(spec=Response)
        validation_response.status_code = HTTPStatus.NO_CONTENT.value

        # Mock successful import response
        import_response = Mock(spec=Response)
        import_response.status_code = HTTPStatus.OK.value

        mock_api.post.side_effect = [validation_response, import_response]

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["prompt_builder.query"]),
            outputs=PipelineOutputs(answers="prompt_builder.prompt"),
            strict_validation=False,
            overwrite=False,
        )

        await pipeline_service.import_async(test_pipeline, config)

        # Check validation call
        validation_call = mock_api.post.call_args_list[0]
        assert validation_call.kwargs["endpoint"] == "pipeline_validations"

        # When overwrite=False, name should be included in validation payload
        validation_json = validation_call.kwargs["json"]
        assert validation_json["name"] == "test_pipeline"
        assert "query_yaml" in validation_json
