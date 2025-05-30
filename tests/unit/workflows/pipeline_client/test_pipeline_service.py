"""Tests for the pipeline service."""
import textwrap
from typing import Any
from unittest.mock import AsyncMock, Mock, call

import pytest
from haystack import AsyncPipeline, Pipeline
from haystack.components.converters import CSVToDocument, TextFileToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.routers import FileTypeRouter
from httpx import Response

from deepset_cloud_sdk._api.config import CommonConfig
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
    _enable_import_into_deepset,
)

from haystack.components.generators import OpenAIGenerator, AzureOpenAIGenerator
from haystack.utils import Secret
import respx


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


class TestEnableImportIntoDeepset:
    """Test suite for the enable_import_into_deepset functionality."""

    def test_enable_import_into_deepset_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful enabling of import into deepset."""
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)

        assert not hasattr(mock_pipeline, "import_into_deepset")
        assert not hasattr(mock_pipeline, "import_into_deepset_async")
        assert not hasattr(mock_async_pipeline, "import_into_deepset")
        assert not hasattr(mock_async_pipeline, "import_into_deepset_async")

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_import_into_deepset(CommonConfig(), "my-workspace")

        # Check sync methods
        assert hasattr(mock_pipeline, "import_into_deepset")
        assert callable(mock_pipeline.import_into_deepset)
        assert hasattr(mock_async_pipeline, "import_into_deepset")
        assert callable(mock_async_pipeline.import_into_deepset)

        # Check async methods
        assert hasattr(mock_pipeline, "import_into_deepset_async")
        assert callable(mock_pipeline.import_into_deepset_async)
        assert hasattr(mock_async_pipeline, "import_into_deepset_async")
        assert callable(mock_async_pipeline.import_into_deepset_async)

    @pytest.mark.asyncio
    async def test_import_into_deepset_async_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the async import into deepset method works correctly."""
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)
        mock_pipeline.import_into_deepset_async = AsyncMock()
        mock_async_pipeline.import_into_deepset_async = AsyncMock()

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        # Test sync Pipeline
        await mock_pipeline.import_into_deepset_async(config)
        mock_pipeline.import_into_deepset_async.assert_called_once_with(config)

        # Test AsyncPipeline
        await mock_async_pipeline.import_into_deepset_async(config)
        mock_async_pipeline.import_into_deepset_async.assert_called_once_with(config)

    def test_import_sync_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the sync import method works correctly."""
        # Create mocks for the pipeline classes
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)

        # Set up the mocks
        mock_pipeline.import_async = AsyncMock()
        mock_async_pipeline.import_async = AsyncMock()

        # Mock PipelineService.import_async to prevent actual execution
        async def mock_service_import_async(self: Any, pipeline: Any, config: PipelineConfig | IndexConfig) -> None:
            await pipeline.import_async(config)

        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.pipeline_client.pipeline_service.PipelineService.import_async",
            mock_service_import_async,
        )
        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_import_into_deepset(CommonConfig(), "my-workspace")

        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(documents="meta_ranker.documents", answers="answer_builder.answers"),
        )

        # Test that calling sync import calls the async method
        # Get the bound method and call it
        import_method = getattr(mock_pipeline, "import_into_deepset")
        import_method(mock_pipeline, config)

        import_method = getattr(mock_async_pipeline, "import_into_deepset")
        import_method(mock_async_pipeline, config)

        # Verify that import_async was called with the correct arguments
        assert mock_pipeline.import_async.call_count == 1
        assert mock_async_pipeline.import_async.call_count == 1
        mock_pipeline.import_async.assert_called_with(config)
        mock_async_pipeline.import_async.assert_called_with(config)

    def test_enable_import_into_deepset_already_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enabling import when the methods already exist."""
        # Mock both Pipeline and AsyncPipeline classes with existing import methods
        mock_pipeline = Mock(spec=Pipeline)
        mock_async_pipeline = Mock(spec=AsyncPipeline)
        existing_import = Mock()
        existing_import_async = Mock()
        mock_pipeline.import_into_deepset = existing_import
        mock_pipeline.import_into_deepset_async = existing_import_async
        mock_async_pipeline.import_into_deepset = existing_import
        mock_async_pipeline.import_into_deepset_async = existing_import_async

        monkeypatch.setattr("haystack.Pipeline", mock_pipeline)
        monkeypatch.setattr("haystack.AsyncPipeline", mock_async_pipeline)

        _enable_import_into_deepset(CommonConfig(), "my-workspace")

        # Verify existing methods weren't overwritten
        assert mock_pipeline.import_into_deepset == existing_import
        assert mock_pipeline.import_into_deepset_async == existing_import_async
        assert mock_async_pipeline.import_into_deepset == existing_import
        assert mock_async_pipeline.import_into_deepset_async == existing_import_async

    def test_enable_import_into_deepset_no_haystack_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enabling import into deepset when haystack-ai is not installed."""

        def mock_import(*args: Any, **kwargs: Any) -> None:
            raise ImportError("Can't import Pipeline or AsyncPipeline.")

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(
            ImportError, match="Can't import Pipeline or AsyncPipeline, because haystack-ai is not installed."
        ):
            _enable_import_into_deepset(CommonConfig(), "my-workspace")


class TestPipelineServiceSecretManagement:
    """Test suite for the PipelineService."""

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
    def pipeline_with_secret(self, monkeypatch: pytest.MonkeyPatch) -> Pipeline:
        """Create a sample pipeline using a secret from the environment."""
        pipeline = Pipeline()
        env_secret_name_1 = "MY_CUSTOM_ENV_VAR_1"
        env_secret_name_2 = "MY_CUSTOM_ENV_VAR_2"
        monkeypatch.setenv(env_secret_name_1, "my-generator-api-key-1")
        monkeypatch.setenv(env_secret_name_2, "my-generator-api-key-2")
        generator = AzureOpenAIGenerator(
            azure_endpoint="https://my-azure-endpoint.openai.azure.com",
            api_key=Secret.from_env_var(env_secret_name_1, strict=False),
            azure_ad_token=Secret.from_env_var(env_secret_name_2, strict=False),
        )
        pipeline.add_component("generator", generator)

        return pipeline

    @pytest.mark.asyncio
    async def test_secrets_are_not_mirrored(
        self,
        pipeline_with_secret: Pipeline,
        pipeline_service: PipelineService,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["llm.query"]),
            outputs=PipelineOutputs(answers="llm.replies"),
        )
        pipeline_yaml = await pipeline_service._from_haystack_pipeline(pipeline_with_secret, config)
        expected_pipeline_yaml = textwrap.dedent(
            """components:
  generator:
    init_parameters:
      api_key:
        env_vars:
        - MY_CUSTOM_ENV_VAR_1
        strict: false
        type: env_var
      api_version: '2023-05-15'
      azure_ad_token:
        env_vars:
        - MY_CUSTOM_ENV_VAR_2
        strict: false
        type: env_var
      azure_ad_token_provider:
      azure_deployment: gpt-4o-mini
      azure_endpoint: https://my-azure-endpoint.openai.azure.com
      default_headers: {}
      generation_kwargs: {}
      http_client_kwargs:
      max_retries: 5
      organization:
      streaming_callback:
      system_prompt:
      timeout: 30.0
    type: haystack.components.generators.azure.AzureOpenAIGenerator
connection_type_validation: true
connections: []
max_runs_per_component: 100
metadata: {}
inputs:
  query:
  - llm.query
outputs:
  answers: llm.replies
"""
        )
        assert pipeline_yaml == expected_pipeline_yaml
        assert "Found secrets MY_CUSTOM_ENV_VAR_1, MY_CUSTOM_ENV_VAR_2 in your pipeline." in caplog.records[0].message

    @pytest.mark.asyncio
    async def test_secrets_are_mirrored(
        self,
        pipeline_with_secret: Pipeline,
        pipeline_service: PipelineService,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that secrets are mirrored when mirror_secrets is True."""
        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["llm.query"]),
            outputs=PipelineOutputs(answers="llm.replies"),
            mirror_secrets=True,
        )

        mock_api = AsyncMock()
        service = PipelineService(mock_api, workspace_name="default")

        await service._from_haystack_pipeline(pipeline_with_secret, config)

        assert mock_api.post.call_count == 2
        mock_api.post.assert_any_call(
            endpoint="api/v2/secrets",
            json={"name": "MY_CUSTOM_ENV_VAR_1", "secret": "my-generator-api-key-1"},
        )
        mock_api.post.assert_any_call(
            endpoint="api/v2/secrets",
            json={"name": "MY_CUSTOM_ENV_VAR_2", "secret": "my-generator-api-key-2"},
        )

    @pytest.mark.asyncio
    async def test_secrets_are_mirrored_missing_env_var(
        self,
        pipeline_with_secret: Pipeline,
        pipeline_service: PipelineService,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that secrets are mirrored when mirror_secrets is True but environment variable is missing."""
        # Remove one of the environment variables
        monkeypatch.delenv("MY_CUSTOM_ENV_VAR_1", raising=False)

        config = PipelineConfig(
            name="test",
            inputs=PipelineInputs(query=["llm.query"]),
            outputs=PipelineOutputs(answers="llm.replies"),
            mirror_secrets=True,
        )

        mock_api = AsyncMock()
        service = PipelineService(mock_api, workspace_name="default")

        await service._from_haystack_pipeline(pipeline_with_secret, config)

        assert mock_api.post.call_count == 1
        mock_api.post.assert_any_call(
            endpoint="api/v2/secrets",
            json={"name": "MY_CUSTOM_ENV_VAR_2", "secret": "my-generator-api-key-2"},
        )

        assert any("Secret 'MY_CUSTOM_ENV_VAR_1' not found in the environment." in record.message for record in caplog.records)
