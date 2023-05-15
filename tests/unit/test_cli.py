from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, patch

import structlog
from typer.testing import CliRunner

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.cli import cli_app

logger = structlog.get_logger(__name__)
runner = CliRunner()


class TestCLI:
    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_file_paths")
    def test_uploading_file_paths(self, async_file_upload_mock: AsyncMock) -> None:
        async def log_file_upload_mock(
            *args: Any,
            **kwargs: Any,
        ) -> None:
            logger.info("Fake log line")

        async_file_upload_mock.side_effect = log_file_upload_mock
        result = runner.invoke(cli_app, ["upload-file-paths", "./test/data/upload_folder/example.txt"])
        assert result.exit_code == 0
        assert "Fake log line" in result.stdout

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_folder")
    def test_uploading_folder(self, async_upload_folder_mock: AsyncMock) -> None:
        def log_upload_folder_mock(
            *args: Any,
            **kwargs: Any,
        ) -> None:
            logger.info("Fake log line")

        async_upload_folder_mock.side_effect = log_upload_folder_mock
        result = runner.invoke(cli_app, ["upload-folder", "./test/data/upload_folder/example.txt"])
        assert result.exit_code == 0
        assert "Fake log line" in result.stdout

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_folder")
    def test_raising_exception_during_cli_run(self, async_upload_folder_mock: AsyncMock) -> None:
        async_upload_folder_mock.side_effect = AssertionError(
            "API_KEY environment variable must be set. Please visit https://cloud.deepset.ai/settings/connections to get an API key."
        )
        result = runner.invoke(cli_app, ["upload-folder", "./test/data/upload_folder/example.txt"])
        assert result.exit_code == 1
