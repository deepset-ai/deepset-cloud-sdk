"""Tests for the DeepsetSDK class."""
from unittest.mock import Mock

import pytest

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk.workflows import DeepsetSDK


class TestDeepsetSDK:
    """Test suite for the DeepsetSDK class."""

    def test_init_with_env_vars_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful SDK initialization with environment variables."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_KEY", "env-api-key")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_URL", "https://env-api-url.com")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.DEFAULT_WORKSPACE_NAME", "test-workspace")
        sdk = DeepsetSDK()
        sdk.init()

        assert isinstance(sdk._config, CommonConfig)
        assert sdk._config.api_key == "env-api-key"
        assert sdk._config.api_url == "https://env-api-url.com"
        assert sdk._workspace_name == "test-workspace"

        mock_enable.assert_called_once()

    def test_init_can_be_called_multiple_times(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that init can be called multiple times safely."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_KEY", "env-api-key")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_URL", "https://env-api-url.com")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.DEFAULT_WORKSPACE_NAME", "test-workspace")

        sdk = DeepsetSDK()
        sdk.init()
        mock_enable.reset_mock()

        sdk.init()

        # _enable_import_into_deepset is called but it's safe to call multiple times
        mock_enable.assert_called_once()

    def test_init_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SDK initialization failure."""
        mock_enable = Mock(side_effect=ImportError("Test error"))
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_KEY", "env-api-key")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_URL", "https://env-api-url.com")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.DEFAULT_WORKSPACE_NAME", "test-workspace")

        sdk = DeepsetSDK()
        with pytest.raises(ImportError, match="Test error"):
            sdk.init()

        mock_enable.assert_called_once()

    def test_init_with_custom_config_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SDK initialization with custom configuration."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)

        sdk = DeepsetSDK(
            api_key="test-api-key-different-from-env",
            workspace_name="test-workspace-different-from-env",
            api_url="https://test-api-url-different-from-env.com",
        )
        sdk.init()

        assert isinstance(sdk._config, CommonConfig)
        assert sdk._config.api_key == "test-api-key-different-from-env"
        assert sdk._config.api_url == "https://test-api-url-different-from-env.com"
        assert sdk._workspace_name == "test-workspace-different-from-env"

        mock_enable.assert_called_once()

    def test_init_with_mixed_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SDK initialization with partial custom configuration."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_URL", "https://env-api-url.com")
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.DEFAULT_WORKSPACE_NAME", "test-workspace")

        sdk = DeepsetSDK(
            api_key="custom-api-key",
        )
        sdk.init()

        assert isinstance(sdk._config, CommonConfig)
        assert sdk._config.api_key == "custom-api-key"
        assert sdk._config.api_url == "https://env-api-url.com"  # From environment
        assert sdk._workspace_name == "test-workspace"  # from environment

        mock_enable.assert_called_once()

    def test_init_calls_enable_import_with_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that SDK init calls _enable_import_into_deepset with correct parameters."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)

        sdk = DeepsetSDK(
            api_key="test-api-key",
            api_url="https://test-api-url.com",
            workspace_name="test-workspace",
        )
        sdk.init()

        mock_enable.assert_called_once()
        args, _ = mock_enable.call_args
        assert isinstance(args[0], CommonConfig)
        assert args[0].api_key == "test-api-key"
        assert args[0].api_url == "https://test-api-url.com"
        assert args[1] == "test-workspace"

    def test_init_with_missing_api_key_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_KEY", "")

        with pytest.raises(AssertionError):
            DeepsetSDK(
                api_url="https://api.com", workspace_name="test-workspace"
            )  # Empty API key should raise AssertionError

    def test_init_with_missing_api_url_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.API_URL", "")

        with pytest.raises(AssertionError):
            DeepsetSDK(api_key="hello")  # Empty API url should raise AssertionError

    def test_init_with_missing_workspace_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk.DEFAULT_WORKSPACE_NAME", "")

        with pytest.raises(ValueError):
            DeepsetSDK(api_key="hello", api_url="https://api.com")  # Empty workspace name should raise ValueError
