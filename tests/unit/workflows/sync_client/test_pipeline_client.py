"""Tests for the PipelineClient class."""

from unittest.mock import AsyncMock, Mock

import pytest
from haystack import AsyncPipeline, Pipeline

from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._service.pipeline_service import PipelineService
from deepset_cloud_sdk.models import (
    IndexConfig,
    IndexInputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)
from deepset_cloud_sdk.workflows.async_client.async_pipeline_client import (
    AsyncPipelineClient,
)
from deepset_cloud_sdk.workflows.sync_client.pipeline_client import PipelineClient


class TestPipelineClientInit:
    """Test suite for the PipelineClient class."""

    def test_init_with_env_vars_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful client initialization with environment variables."""
        monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_KEY", "env-api-key")
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_URL", "https://env-api-url.com"
        )
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.DEFAULT_WORKSPACE_NAME", "test-workspace"
        )
        pc = PipelineClient()

        assert isinstance(pc._async_client, AsyncPipelineClient)
        assert pc._async_client._api_config.api_key == "env-api-key"
        assert pc._async_client._api_config.api_url == "https://env-api-url.com"
        assert pc._async_client._workspace_name == "test-workspace"

    def test_init_with_explicit_api_config_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client initialization with explicit api configuration."""
        pc = PipelineClient(
            api_key="test-api-key-explicit",
            workspace_name="test-workspace-explicit",
            api_url="https://test-api-url-explicit.com",
        )

        assert isinstance(pc._async_client, AsyncPipelineClient)
        assert pc._async_client._api_config.api_key == "test-api-key-explicit"
        assert pc._async_client._api_config.api_url == "https://test-api-url-explicit.com"
        assert pc._async_client._workspace_name == "test-workspace-explicit"


class TestPipelineClientImport:
    """Test suite for importing Haystack pipelines into deepset."""

    @pytest.fixture
    def mock_api_service_setup(self, monkeypatch: pytest.MonkeyPatch) -> dict:
        """Fixture to set up mocked API and service components."""
        mock_api = Mock(spec=DeepsetCloudAPI)
        mock_service = Mock(spec=PipelineService)
        mock_service.import_async = AsyncMock()

        # Create a proper async context manager mock
        mock_api_context = AsyncMock()
        mock_api_context.__aenter__ = AsyncMock(return_value=mock_api)
        mock_api_context.__aexit__ = AsyncMock(return_value=None)

        mock_api_factory = Mock(return_value=mock_api_context)
        mock_pipeline_service = Mock(return_value=mock_service)

        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.DeepsetCloudAPI.factory", mock_api_factory
        )
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.PipelineService", mock_pipeline_service
        )

        return {
            "api": mock_api,
            "service": mock_service,
            "api_factory": mock_api_factory,
            "pipeline_service": mock_pipeline_service,
        }

    @pytest.fixture
    def client_with_explicit_config(self) -> PipelineClient:
        """Fixture to create client instance with explicit configuration."""
        return PipelineClient(api_key="test-key", api_url="https://test.com", workspace_name="test-workspace")

    @pytest.fixture
    def index_config(self) -> IndexConfig:
        """Fixture to create an IndexConfig."""
        return IndexConfig(
            name="test_index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
        )

    @pytest.fixture
    def pipeline_config(self) -> PipelineConfig:
        """Fixture to create a PipelineConfig."""
        return PipelineConfig(
            name="test_pipeline",
            inputs=PipelineInputs(query=["retriever.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
        )

    @pytest.mark.parametrize("pipeline_type", [Pipeline, AsyncPipeline])
    def test_import_into_deepset_and_index_config_success(
        self,
        pipeline_type: Pipeline | AsyncPipeline,
        mock_api_service_setup: dict,
        client_with_explicit_config: PipelineClient,
        index_config: IndexConfig,
    ) -> None:
        """Test successful sync import of pipeline with IndexConfig."""
        mock_pipeline = Mock(spec=pipeline_type)

        client_with_explicit_config.import_into_deepset(mock_pipeline, index_config)

        mock_api_service_setup["api_factory"].assert_called_once_with(
            client_with_explicit_config._async_client._api_config
        )
        mock_api_service_setup["pipeline_service"].assert_called_once_with(
            mock_api_service_setup["api"], "test-workspace"
        )
        mock_api_service_setup["service"].import_async.assert_called_once_with(mock_pipeline, index_config)

    @pytest.mark.parametrize("pipeline_type", [Pipeline, AsyncPipeline])
    def test_import_into_deepset_and_pipeline_config_success(
        self,
        pipeline_type: Pipeline | AsyncPipeline,
        mock_api_service_setup: dict,
        client_with_explicit_config: PipelineClient,
        pipeline_config: PipelineConfig,
    ) -> None:
        """Test successful sync import of pipeline with PipelineConfig."""
        mock_pipeline = Mock(spec=pipeline_type)

        client_with_explicit_config.import_into_deepset(mock_pipeline, pipeline_config)

        mock_api_service_setup["api_factory"].assert_called_once_with(
            client_with_explicit_config._async_client._api_config
        )
        mock_api_service_setup["pipeline_service"].assert_called_once_with(
            mock_api_service_setup["api"], "test-workspace"
        )
        mock_api_service_setup["service"].import_async.assert_called_once_with(mock_pipeline, pipeline_config)

    def test_import_into_deepset_with_no_event_loop(
        self,
        client_with_explicit_config: PipelineClient,
        index_config: IndexConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test sync import when no event loop exists."""
        mock_pipeline = Mock(spec=Pipeline)

        mock_import_into_deepset = AsyncMock()
        monkeypatch.setattr(
            client_with_explicit_config._async_client,
            "import_into_deepset",
            mock_import_into_deepset,
        )

        # Mock new_event_loop and set_event_loop
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = None
        mock_loop.close = Mock()

        monkeypatch.setattr(
            "asyncio.get_event_loop", Mock(side_effect=RuntimeError("There is no current event loop in thread"))
        )
        monkeypatch.setattr("asyncio.new_event_loop", Mock(return_value=mock_loop))
        monkeypatch.setattr("asyncio.set_event_loop", Mock())

        client_with_explicit_config.import_into_deepset(mock_pipeline, index_config)

        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()

        mock_import_into_deepset.assert_called_once_with(mock_pipeline, index_config)

    def test_import_into_deepset_with_existing_event_loop(
        self,
        client_with_explicit_config: PipelineClient,
        index_config: IndexConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test sync import when event loop already exists."""
        mock_pipeline = Mock(spec=Pipeline)

        mock_import_into_deepset = AsyncMock()
        monkeypatch.setattr(
            client_with_explicit_config._async_client,
            "import_into_deepset",
            mock_import_into_deepset,
        )

        mock_loop = Mock()
        mock_loop.is_closed.return_value = False
        mock_loop.run_until_complete.return_value = None
        mock_loop.close = Mock()

        monkeypatch.setattr("asyncio.get_event_loop", Mock(return_value=mock_loop))

        client_with_explicit_config.import_into_deepset(mock_pipeline, index_config)

        # Verify that existing loop was used and NOT closed
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_not_called()

        mock_import_into_deepset.assert_called_once_with(mock_pipeline, index_config)
