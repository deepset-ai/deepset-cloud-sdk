import datetime
import os
from pathlib import Path
from typing import Any, Generator, List
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

import structlog
import typer
from typer.testing import CliRunner

from deepset_cloud_sdk.__about__ import __version__
from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.files import File
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

    @patch("deepset_cloud_sdk.cli.sync_list_files")
    def test_listing_files(self, sync_list_files_mock: AsyncMock) -> None:
        def mocked_list_files(
            *args: Any,
            **kwargs: Any,
        ) -> Generator[List[File], None, None]:
            yield [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]

        sync_list_files_mock.side_effect = mocked_list_files
        result = runner.invoke(cli_app, ["list-files"])
        assert result.exit_code == 0
        assert (
            " cd16435f-f6eb-423f-bf6f-994dc8a36a10 | /api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10 | silly_things_1.txt |    611 | 2022-06-21 16:40:00.634653+00:00 | {}  "
            in result.stdout
        )

    @patch("deepset_cloud_sdk.cli.sync_list_files")
    def test_listing_files_with_no_found_files(self, sync_list_files_mock: AsyncMock) -> None:
        def mocked_list_files(
            *args: Any,
            **kwargs: Any,
        ) -> Generator[List[File], None, None]:
            yield []

        sync_list_files_mock.side_effect = mocked_list_files
        result = runner.invoke(cli_app, ["list-files"])
        assert result.exit_code == 0
        assert (
            "+-----------+-------+--------+--------+--------------+--------+\n| file_id   | url   | name   | size   | created_at   | meta   |\n+===========+=======+========+========+==============+========+\n+-----------+-------+--------+--------+--------------+--------+\n"
            in result.stdout
        )

    @patch("deepset_cloud_sdk.cli.sync_list_files")
    def test_listing_files_with_cut_off(self, sync_list_files_mock: AsyncMock) -> None:
        def mocked_list_files(
            *args: Any,
            **kwargs: Any,
        ) -> Generator[List[File], None, None]:
            yield [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]
            yield [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]

        sync_list_files_mock.side_effect = mocked_list_files
        result = runner.invoke(cli_app, ["list-files", "--batch-size", "1"], input="y")
        assert result.exit_code == 0
        # check that two batches are printed
        assert (
            "+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\n| file_id                              | url                                                                        | name               |   size | created_at                       | meta   |\n+======================================+============================================================================+====================+========+==================================+========+\n| cd16435f-f6eb-423f-bf6f-994dc8a36a10 | /api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10 | silly_things_1.txt |    611 | 2022-06-21 16:40:00.634653+00:00 | {}     |\n+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\nPrint more results ? [y]: y\n+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\n| file_id                              | url                                                                        | name               |   size | created_at                       | meta   |\n+======================================+============================================================================+====================+========+==================================+========+\n| cd16435f-f6eb-423f-bf6f-994dc8a36a10 | /api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10 | silly_things_1.txt |    611 | 2022-06-21 16:40:00.634653+00:00 | {}     |\n+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\nPrint more results ? [y]: \n"
            == result.stdout
        )

    @patch("deepset_cloud_sdk.cli.sync_list_files")
    def test_listing_files_with_break_showing_more_results(self, sync_list_files_mock: AsyncMock) -> None:
        def mocked_list_files(
            *args: Any,
            **kwargs: Any,
        ) -> Generator[List[File], None, None]:
            yield [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]
            yield [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]

        sync_list_files_mock.side_effect = mocked_list_files
        result = runner.invoke(cli_app, ["list-files", "--batch-size", "1"], input="n")
        assert result.exit_code == 0
        # check that two batches are printed
        assert (
            "+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\n| file_id                              | url                                                                        | name               |   size | created_at                       | meta   |\n+======================================+============================================================================+====================+========+==================================+========+\n| cd16435f-f6eb-423f-bf6f-994dc8a36a10 | /api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10 | silly_things_1.txt |    611 | 2022-06-21 16:40:00.634653+00:00 | {}     |\n+--------------------------------------+----------------------------------------------------------------------------+--------------------+--------+----------------------------------+--------+\nPrint more results ? [y]: n\n"
            == result.stdout
        )


class TestCLIUtils:
    def test_login_with_minimal(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["login"], input="test_api_key\n\n\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key\nAPI_URL=https://api.cloud.deepset.ai/api/v1\nDEFAULT_WORKSPACE_NAME=default"
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

    def test_logout_if_not_logged_in(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["logout"])
            assert result.exit_code == 0
            assert "You are not logged in. Nothing to do!" in result.stdout

    @patch("deepset_cloud_sdk.cli.os")
    def test_logout(self, mocked_os: Mock) -> None:
        mocked_os.path.exists.return_value = True

        result = runner.invoke(cli_app, ["logout"])
        assert result.exit_code == 0
        assert "removed successfully" in result.stdout

    def test_get_version(self) -> None:
        result = runner.invoke(cli_app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout
