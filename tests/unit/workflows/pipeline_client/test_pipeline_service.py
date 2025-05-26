"""Tests for the pipeline service."""
import textwrap
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from haystack import AsyncPipeline, Pipeline
from haystack.components.converters import CSVToDocument, TextFileToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.routers import FileTypeRouter

from deepset_cloud_sdk.workflows import DeepsetSDK
from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)
from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    PipelineService,
    _enable_publish_to_deepset,
)


class TestPublishPipelineService:
    """Test suite for the PipelineService publish functionality."""

    @pytest.fixture
    def mock_api(self) -> AsyncMock:
        """Create a mock API client."""
        mock = AsyncMock()
        mock.post.return_value = Mock(status_code=201)
        return mock

    @pytest.fixture
    def pipeline_service(self, mock_api: AsyncMock) -> PipelineService:
        """Create a pipeline service instance with a mock API client."""
        return PipelineService(mock_api)

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
    async def test_publish_index(
        self,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        mock_api: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test publishing an index pipeline."""
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.DEFAULT_WORKSPACE_NAME", "default"
        )

        # Create publish config
        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
        )

        # Publish the pipeline
        await pipeline_service.publish_async(index_pipeline, config)

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
    async def test_publish_index_pipeline_with_invalid_pipeline(self, pipeline_service: PipelineService) -> None:
        """Test publishing unexpected pipeline object."""
        config = IndexConfig(name="test_index", inputs=IndexInputs(files=["my_component.files"]))

        # Create an invalid pipeline (doesn't implement PipelineProtocol)
        invalid_pipeline = object()

        with pytest.raises(TypeError, match="Haystack Pipeline or AsyncPipeline object expected.*"):
            await pipeline_service.publish_async(invalid_pipeline, config)  # type: ignore

    @pytest.mark.parametrize("empty_value", ["", None])
    @pytest.mark.asyncio
    async def test_publish_index_pipeline_without_workspace(
        self,
        empty_value: Any,
        pipeline_service: PipelineService,
        index_pipeline: Pipeline,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test publishing an index pipeline without workspace configuration."""
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.DEFAULT_WORKSPACE_NAME", empty_value
        )
        config = IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_classifier.sources"]),
        )

        with pytest.raises(ValueError, match="We couldn't find the workspace"):
            await pipeline_service.publish_async(index_pipeline, config)

    @pytest.mark.asyncio
    async def test_publish_pipeline_with_outputs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test publishing a pipeline."""
        mock_api = AsyncMock()
        service = PipelineService(mock_api)
        mock_pipeline = Mock(spec=Pipeline)
        mock_pipeline.dumps.return_value = textwrap.dedent(
            """components:
  retriever:
    type: haystack.components.retrievers.in_memory.InMemoryBM25Retriever
"""
        )
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.DEFAULT_WORKSPACE_NAME", "default"
        )

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        await service.publish_async(mock_pipeline, config)
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
    async def test_publish_pipeline_import_error(
        self, pipeline_service: PipelineService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test publishing a pipeline when haystack-ai is not installed."""

        def mock_import(*args: Any, **kwargs: Any) -> None:
            raise ImportError("Can't import Pipeline or AsyncPipeline.")

        monkeypatch.setattr("builtins.__import__", mock_import)

        config = PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        with pytest.raises(
            ImportError, match="Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed."
        ):
            await pipeline_service.publish_async(Mock(), config)

    @pytest.mark.asyncio
    async def test_publish_index_with_outputs_and_additional_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test publishing an index with outputs and additional input parameters."""
        mock_api = AsyncMock()
        service = PipelineService(mock_api)
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.DEFAULT_WORKSPACE_NAME", "default"
        )
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

        await service.publish_async(mock_pipeline, config)
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
            workspace_name="default",
            endpoint="indexes",
            json={"name": "test_index", "config_yaml": expected_pipeline_yaml},
        )


class TestEnablePublishToDeepset:
    """Test suite for the enable_publish_to_deepset functionality."""

    def test_enable_publish_to_deepset_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful enabling of publish to deepset."""
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)

        assert not hasattr(mock_pipeline, "publish")
        assert not hasattr(mock_pipeline, "publish_async")
        assert not hasattr(mock_async_pipeline, "publish")
        assert not hasattr(mock_async_pipeline, "publish_async")

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_publish_to_deepset()

        # Check sync methods
        assert hasattr(mock_pipeline, "publish")
        assert callable(mock_pipeline.publish)
        assert hasattr(mock_async_pipeline, "publish")
        assert callable(mock_async_pipeline.publish)

        # Check async methods
        assert hasattr(mock_pipeline, "publish_async")
        assert callable(mock_pipeline.publish_async)
        assert hasattr(mock_async_pipeline, "publish_async")
        assert callable(mock_async_pipeline.publish_async)

    @pytest.mark.asyncio
    async def test_publish_async_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the async publish method works correctly."""
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)
        mock_pipeline.publish_async = AsyncMock()
        mock_async_pipeline.publish_async = AsyncMock()

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        # Test sync Pipeline
        await mock_pipeline.publish_async(config)
        mock_pipeline.publish_async.assert_called_once_with(config)

        # Test AsyncPipeline
        await mock_async_pipeline.publish_async(config)
        mock_async_pipeline.publish_async.assert_called_once_with(config)

    def test_publish_sync_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the sync publish method works correctly."""
        # Create mocks for the pipeline classes
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)

        # Set up the mocks
        mock_pipeline.publish_async = AsyncMock()
        mock_async_pipeline.publish_async = AsyncMock()

        # Mock PipelineService.publish_async to prevent actual execution
        async def mock_service_publish_async(self: Any, pipeline: Any, config: PipelineConfig | IndexConfig) -> None:
            await pipeline.publish_async(config)

        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.PipelineService.publish_async",
            mock_service_publish_async,
        )
        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_publish_to_deepset()

        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        # Test that calling sync publish calls the async method
        # Get the bound method and call it
        publish_method = getattr(mock_pipeline, "publish")
        publish_method(mock_pipeline, config)

        publish_method = getattr(mock_async_pipeline, "publish")
        publish_method(mock_async_pipeline, config)

        # Verify that publish_async was called with the correct arguments
        assert mock_pipeline.publish_async.call_count == 1
        assert mock_async_pipeline.publish_async.call_count == 1
        mock_pipeline.publish_async.assert_called_with(config)
        mock_async_pipeline.publish_async.assert_called_with(config)

    def test_enable_publish_to_deepset_already_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enabling publish when the methods already exist."""
        # Mock both Pipeline and AsyncPipeline classes with existing publish methods
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)
        existing_publish = Mock()
        existing_publish_async = Mock()
        mock_pipeline.publish = existing_publish
        mock_pipeline.publish_async = existing_publish_async
        mock_async_pipeline.publish = existing_publish
        mock_async_pipeline.publish_async = existing_publish_async

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_publish_to_deepset()

        # Verify existing methods weren't overwritten
        assert mock_pipeline.publish == existing_publish
        assert mock_pipeline.publish_async == existing_publish_async
        assert mock_async_pipeline.publish == existing_publish
        assert mock_async_pipeline.publish_async == existing_publish_async

    def test_enable_publish_to_deepset_no_haystack_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enabling publish when haystack-ai is not installed."""

        def mock_import(*args: Any, **kwargs: Any) -> None:
            raise ImportError("Can't import Pipeline or AsyncPipeline.")

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(
            ImportError, match="Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed."
        ):
            _enable_publish_to_deepset()
