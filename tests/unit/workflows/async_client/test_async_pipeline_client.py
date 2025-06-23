"""Tests for the AsyncPipelineClient class."""

from unittest.mock import AsyncMock, Mock

import pytest
from haystack import AsyncPipeline, Pipeline

from deepset_cloud_sdk._api.config import CommonConfig
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


class TestAsyncPipelineClientInit:
    """Test suite for the AsyncPipelineClient class."""

    def test_init_with_env_vars_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful client initialization with environment variables."""
        monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_KEY", "env-api-key")
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_URL", "https://env-api-url.com"
        )
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.DEFAULT_WORKSPACE_NAME", "test-workspace"
        )
        pc = AsyncPipelineClient()

        assert isinstance(pc._api_config, CommonConfig)
        assert pc._api_config.api_key == "env-api-key"
        assert pc._api_config.api_url == "https://env-api-url.com"
        assert pc._workspace_name == "test-workspace"

    def test_init_with_explicit_api_config_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client initialization with explicit api configuration."""
        pc = AsyncPipelineClient(
            api_key="test-api-key-explicit",
            workspace_name="test-workspace-explicit",
            api_url="https://test-api-url-explicit.com",
        )

        assert isinstance(pc._api_config, CommonConfig)
        assert pc._api_config.api_key == "test-api-key-explicit"
        assert pc._api_config.api_url == "https://test-api-url-explicit.com"
        assert pc._workspace_name == "test-workspace-explicit"

    def test_init_with_mixed_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client initialization with partial explicit configuration."""
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_URL", "https://env-api-url.com"
        )
        monkeypatch.setattr(
            "deepset_cloud_sdk.workflows.async_client.async_pipeline_client.DEFAULT_WORKSPACE_NAME", "test-workspace"
        )

        pc = AsyncPipelineClient(
            api_key="custom-api-key",
        )

        assert isinstance(pc._api_config, CommonConfig)
        assert pc._api_config.api_key == "custom-api-key"
        assert pc._api_config.api_url == "https://env-api-url.com"  # From environment
        assert pc._workspace_name == "test-workspace"  # from environment

    def test_init_with_missing_api_key_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Remove both environment variable and global variable that was loaded at import time
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_KEY", "")

        with pytest.raises(ValueError):
            AsyncPipelineClient(
                api_url="https://api.com", workspace_name="test-workspace"
            )  # Empty API key should raise ValueError

    def test_init_with_missing_api_url_uses_default_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.async_pipeline_client.API_URL", "")

        pc = AsyncPipelineClient(api_key="hello", api_url="", workspace_name="test-workspace")

        assert pc._api_config.api_url == "https://api.cloud.deepset.ai/api/v1"

    def test_init_with_missing_workspace_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.async_pipeline_client.DEFAULT_WORKSPACE_NAME", "")

        with pytest.raises(ValueError):
            AsyncPipelineClient(
                api_key="hello", api_url="https://api.com"
            )  # Empty workspace name should raise ValueError


class TestAsyncPipelineClientImport:
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
    def client_with_explicit_config(self) -> AsyncPipelineClient:
        """Fixture to create client instance with explicit configuration."""
        return AsyncPipelineClient(api_key="test-key", api_url="https://test.com", workspace_name="test-workspace")

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

    @pytest.mark.asyncio
    @pytest.mark.parametrize("pipeline_type", [Pipeline, AsyncPipeline])
    async def test_import_into_deepset_async_and_index_config_success(
        self,
        pipeline_type: Pipeline | AsyncPipeline,
        mock_api_service_setup: dict,
        client_with_explicit_config: AsyncPipelineClient,
        index_config: IndexConfig,
    ) -> None:
        """Test successful async import of pipeline with IndexConfig."""
        mock_pipeline = Mock(spec=pipeline_type)

        await client_with_explicit_config.import_into_deepset(mock_pipeline, index_config)

        mock_api_service_setup["api_factory"].assert_called_once_with(client_with_explicit_config._api_config)
        mock_api_service_setup["pipeline_service"].assert_called_once_with(
            mock_api_service_setup["api"], "test-workspace"
        )
        mock_api_service_setup["service"].import_async.assert_called_once_with(mock_pipeline, index_config)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("pipeline_type", [Pipeline, AsyncPipeline])
    async def test_import_into_deepset_async_and_pipeline_config_success(
        self,
        pipeline_type: Pipeline | AsyncPipeline,
        mock_api_service_setup: dict,
        client_with_explicit_config: AsyncPipelineClient,
        pipeline_config: PipelineConfig,
    ) -> None:
        """Test successful async import of pipeline with PipelineConfig."""
        mock_pipeline = Mock(spec=pipeline_type)

        await client_with_explicit_config.import_into_deepset(mock_pipeline, pipeline_config)

        mock_api_service_setup["api_factory"].assert_called_once_with(client_with_explicit_config._api_config)
        mock_api_service_setup["pipeline_service"].assert_called_once_with(
            mock_api_service_setup["api"], "test-workspace"
        )
        mock_api_service_setup["service"].import_async.assert_called_once_with(mock_pipeline, pipeline_config)
