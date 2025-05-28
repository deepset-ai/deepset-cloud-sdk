"""Tests for the DeepsetSDK class."""
from unittest.mock import Mock

import pytest

from deepset_cloud_sdk.workflows import DeepsetSDK


class TestDeepsetSDK:
    """Test suite for the DeepsetSDK class."""

    def test_init_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful SDK initialization."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)

        sdk = DeepsetSDK()
        sdk.init()

        mock_enable.assert_called_once()

    def test_init_can_be_called_multiple_times(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that init can be called multiple times safely."""
        mock_enable = Mock()
        monkeypatch.setattr("deepset_cloud_sdk.workflows.sdk._enable_import_into_deepset", mock_enable)

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

        sdk = DeepsetSDK()
        with pytest.raises(ImportError, match="Test error"):
            sdk.init()

        mock_enable.assert_called_once()
