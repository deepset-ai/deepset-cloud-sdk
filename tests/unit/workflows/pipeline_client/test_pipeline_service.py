"""Tests for the pipeline service."""
import textwrap
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from haystack import Pipeline
from haystack.components.converters import CSVToDocument, TextFileToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.routers import FileTypeRouter

from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)
from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import PipelineService


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
    async def test_import_index_pipeline_with_invalid_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test importing unexpected pipeline object."""
        config = IndexConfig(name="test_index", inputs=IndexInputs(files=["my_component.files"]))

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

        import builtins

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
