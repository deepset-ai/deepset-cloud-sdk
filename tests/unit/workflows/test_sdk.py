"""Tests for the DeepsetSDK class."""
from unittest.mock import Mock

import pytest

from deepset_cloud_sdk.workflows import DeepsetSDK


class TestDeepsetSDK:
    """Test suite for the DeepsetSDK class."""

    def test_init_not_initialized_by_default(self) -> None:
        """Test that SDK is not initialized by default."""
        sdk = DeepsetSDK()
        assert sdk.is_initialized is False

    def test_init_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful SDK initialization."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_publish_to_deepset", mock_enable)

        sdk = DeepsetSDK()
        sdk.init()

        mock_enable.assert_called_once()
        assert sdk.is_initialized is True

    def test_init_already_initialized(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that init does nothing if already initialized."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_publish_to_deepset", mock_enable)

        sdk = DeepsetSDK()
        sdk.init()
        mock_enable.reset_mock()

        sdk.init()

        mock_enable.assert_not_called()
        assert sdk.is_initialized is True

    def test_init_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SDK initialization failure."""
        mock_enable = Mock(side_effect=ImportError("Test error"))
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_publish_to_deepset", mock_enable)

        sdk = DeepsetSDK()
        sdk.init()

        mock_enable.assert_called_once()
        assert sdk.is_initialized is False
