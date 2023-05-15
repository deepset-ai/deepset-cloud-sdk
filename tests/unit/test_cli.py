from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock, patch

import structlog
from typer.testing import CliRunner

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.cli import cli_app, run_packaged

logger = structlog.get_logger(__name__)
runner = CliRunner()


class TestCLIMethods:
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

    def test_run_packaged(
        self,
    ) -> None:
        mocked_cli_app = Mock()
        with patch("deepset_cloud_sdk.cli.cli_app", mocked_cli_app):
            run_packaged()
            assert mocked_cli_app.called

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


class TestCLIUtils:
    def test_login_with_minimal(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["login"], input="test_api_key\n\n\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key\nAPI_URL=https://api.cloud.deepset.ai/api/v1/\nDEFAULT_WORKSPACE_NAME=default"
                    == f.read()
                )

    def test_login_with_all_filled(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["login"], input="test_api_key_2\nhttps://endpoint.com/api\ndefault\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key_2\nAPI_URL=https://endpoint.com/api\nDEFAULT_WORKSPACE_NAME=default"
                    == f.read()
                )
