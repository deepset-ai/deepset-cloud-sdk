import datetime
from pathlib import Path
from typing import Any, Generator, List
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

import structlog
from typer.testing import CliRunner

from deepset_cloud_sdk.__about__ import __version__
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSessionDetail,
    UploadSessionStatusEnum,
    UploadSessionWriteModeEnum,
)
from deepset_cloud_sdk.cli import cli_app
from deepset_cloud_sdk.models import UserInfo

logger = structlog.get_logger(__name__)
runner = CliRunner()


class TestCLIMethods:
    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload")
    def test_uploading(self, async_upload_mock: AsyncMock) -> None:
        def log_upload_folder_mock(
            *args: Any,
            **kwargs: Any,
        ) -> None:
            logger.info("Fake log line")

        async_upload_mock.side_effect = log_upload_folder_mock
        result = runner.invoke(cli_app, ["upload", "./test/data/upload_folder/example.txt"])
        assert result.exit_code == 0
        assert "Fake log line" in result.stdout

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload")
    def test_raising_exception_during_cli_run(self, async_upload_mock: AsyncMock) -> None:
        async_upload_mock.side_effect = AssertionError(
            "API_KEY environment variable must be set. Please visit https://cloud.deepset.ai/settings/connections to get an API key."
        )
        result = runner.invoke(cli_app, ["upload", "./test/data/upload_folder/example.txt"])
        assert result.exit_code == 1

    class TestListFiles:
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

    class TestListUploadSessions:
        @patch("deepset_cloud_sdk.cli.sync_list_upload_sessions")
        def test_listing_upload_sessions(self, sync_list_upload_sessions: AsyncMock) -> None:
            def mocked_list_upload_sessions(
                *args: Any,
                **kwargs: Any,
            ) -> Generator[List[UploadSessionDetail], None, None]:
                yield [
                    UploadSessionDetail(
                        session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                        created_by=UserInfo(
                            user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            given_name="Fake",
                            family_name="User",
                        ),
                        expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                        created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                        write_mode=UploadSessionWriteModeEnum.KEEP,
                        status=UploadSessionStatusEnum.OPEN,
                    )
                ]

            sync_list_upload_sessions.side_effect = mocked_list_upload_sessions
            result = runner.invoke(cli_app, ["list-upload-sessions"])
            assert result.exit_code == 0
            assert (
                "cd16435f-f6eb-423f-bf6f-994dc8a36a10 | UserInfo(user_id=UUID('cd16435f-f6eb-423f-bf6f-994dc8a36a10'), given_name='Fake', family_name='User') | 2022-06-21 16:10:00.634653+00:00 | 2022-06-21 16:40:00.634653+00:00 | KEEP         | OPEN"
                in result.stdout
            )

        @patch("deepset_cloud_sdk.cli.sync_list_upload_sessions")
        def test_listing_upload_sessions_with_break(self, sync_list_upload_sessions: AsyncMock) -> None:
            def mocked_list_upload_sessions(
                *args: Any,
                **kwargs: Any,
            ) -> Generator[List[UploadSessionDetail], None, None]:
                yield [
                    UploadSessionDetail(
                        session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                        created_by=UserInfo(
                            user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            given_name="Fake",
                            family_name="User",
                        ),
                        expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                        created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                        write_mode=UploadSessionWriteModeEnum.KEEP,
                        status=UploadSessionStatusEnum.OPEN,
                    )
                ]
                yield [
                    UploadSessionDetail(
                        session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                        created_by=UserInfo(
                            user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            given_name="Not In There",
                            family_name="Not In There",
                        ),
                        expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                        created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                        write_mode=UploadSessionWriteModeEnum.KEEP,
                        status=UploadSessionStatusEnum.OPEN,
                    ),
                ]

            sync_list_upload_sessions.side_effect = mocked_list_upload_sessions
            result = runner.invoke(cli_app, ["list-upload-sessions", "--batch-size", "1"], input="n")
            assert result.exit_code == 0
            assert "Not In There" not in result.stdout


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
            result = runner.invoke(cli_app, ["login"], input="test_api_key_2\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key_2\nAPI_URL=https://api.cloud.deepset.ai/api/v1\nDEFAULT_WORKSPACE_NAME=default"
                    == f.read()
                )

    @patch("deepset_cloud_sdk.cli.os")
    def test_logout_if_not_logged_in(self, mocked_os: Mock) -> None:
        mocked_os.path.exists.return_value = False
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
