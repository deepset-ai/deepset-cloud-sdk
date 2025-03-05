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
    UploadSessionIngestionStatus,
    UploadSessionStatus,
    UploadSessionStatusEnum,
    UploadSessionWriteModeEnum,
    WriteMode,
)
from deepset_cloud_sdk.cli import cli_app
from deepset_cloud_sdk.models import UserInfo
from deepset_cloud_sdk.workflows.sync_client.files import download as sync_download

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

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload")
    def test_upload_only_desired_file_types_defaults_to_text(self, async_upload_mock: AsyncMock) -> None:
        result = runner.invoke(
            cli_app,
            [
                "upload",
                "./test/data/upload_folder/example.txt",
                "--workspace-name",
                "default",
                "--enable-parallel-processing",
            ],
        )
        async_upload_mock.assert_called_once_with(
            paths=[Path("test/data/upload_folder/example.txt")],
            api_key=None,
            api_url=None,
            workspace_name="default",
            write_mode=WriteMode.KEEP,
            blocking=True,
            timeout_s=None,
            show_progress=True,
            recursive=False,
            desired_file_types=None,
            enable_parallel_processing=True,
            safe_mode=False,
        )
        assert result.exit_code == 0

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload")
    def test_upload_only_desired_file_types_with_desired_file_types(self, async_upload_mock: AsyncMock) -> None:
        result = runner.invoke(
            cli_app,
            [
                "upload",
                "./test/data/upload_folder/example.txt",
                "--workspace-name",
                "default",
                "--use-type",
                ".csv",
                "--use-type",
                ".pdf",
                "--use-type",
                ".json",
                "--use-type",
                ".xml",
            ],
        )
        async_upload_mock.assert_called_once_with(
            paths=[Path("test/data/upload_folder/example.txt")],
            api_key=None,
            api_url=None,
            workspace_name="default",
            write_mode=WriteMode.KEEP,
            blocking=True,
            timeout_s=None,
            show_progress=True,
            recursive=False,
            desired_file_types=[".csv", ".pdf", ".json", ".xml"],
            enable_parallel_processing=False,
            safe_mode=False,
        )
        assert result.exit_code == 0

    @patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload")
    def test_upload_safe_mode(self, async_upload_mock: AsyncMock) -> None:
        result = runner.invoke(
            cli_app,
            [
                "upload",
                "./test/data/upload_folder/example.txt",
                "--workspace-name",
                "default",
                "--safe-mode",
            ],
        )
        async_upload_mock.assert_called_once_with(
            paths=[Path("test/data/upload_folder/example.txt")],
            api_key=None,
            api_url=None,
            workspace_name="default",
            write_mode=WriteMode.KEEP,
            blocking=True,
            timeout_s=None,
            show_progress=True,
            recursive=False,
            desired_file_types=None,
            enable_parallel_processing=False,
            safe_mode=True,
        )
        assert result.exit_code == 0

    class TestDownloadFiles:
        @patch("deepset_cloud_sdk.cli.sync_download")
        def test_download_files(self, sync_download_mock: AsyncMock) -> None:
            sync_download_mock.side_effect = Mock(spec=sync_download)
            result = runner.invoke(cli_app, ["download", "--workspace-name", "default"])
            assert result.exit_code == 0
            sync_download_mock.assert_called_once_with(
                workspace_name="default",
                file_dir=None,
                name=None,
                odata_filter=None,
                include_meta=True,
                batch_size=50,
                api_key=None,
                api_url=None,
                show_progress=True,
                safe_mode=False,
            )

        @patch("deepset_cloud_sdk.cli.sync_download")
        def test_download_files_safe_mode(self, sync_download_mock: AsyncMock) -> None:
            sync_download_mock.side_effect = Mock(spec=sync_download)
            result = runner.invoke(cli_app, ["download", "--workspace-name", "default", "--safe-mode"])
            assert result.exit_code == 0
            sync_download_mock.assert_called_once_with(
                workspace_name="default",
                file_dir=None,
                name=None,
                odata_filter=None,
                include_meta=True,
                batch_size=50,
                api_key=None,
                api_url=None,
                show_progress=True,
                safe_mode=True,
            )

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
        def test_listing_files_with_timeout(self, sync_list_files_mock: AsyncMock) -> None:
            sync_list_files_mock.side_effect = TimeoutError()
            result = runner.invoke(cli_app, ["list-files"])
            assert result.exit_code == 0
            assert "Command timed out." in result.stdout

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
                "cd16435f-f6eb-423f-bf6f-994dc8a36a10 | Fake User    | 2022-06-21 16:10:00.634653+00:00 | 2022-06-21 16:40:00.634653+00:00 | KEEP         | OPEN"
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

        @patch("deepset_cloud_sdk.cli.sync_list_upload_sessions")
        def test_listing_files_with_timeout(self, sync_list_upload_sessions: AsyncMock) -> None:
            sync_list_upload_sessions.side_effect = TimeoutError()
            result = runner.invoke(cli_app, ["list-upload-sessions"])
            assert result.exit_code == 0
            assert "Command timed out." in result.stdout

    class TestGetUploadSession:
        @patch("deepset_cloud_sdk.cli.sync_get_upload_session")
        def test_get_upload_session(self, sync_get_upload_session: AsyncMock) -> None:
            def mocked_get_upload_session(
                *args: Any,
                **kwargs: Any,
            ) -> UploadSessionStatus:
                return UploadSessionStatus(
                    session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                    documentation_url="https://docs.deepset.ai",
                    ingestion_status=UploadSessionIngestionStatus(
                        failed_files=0,
                        finished_files=1,
                    ),
                )

            sync_get_upload_session.side_effect = mocked_get_upload_session
            result = runner.invoke(cli_app, ["get-upload-session", "cd16435f-f6eb-423f-bf6f-994dc8a36a10"])
            assert result.exit_code == 0
            assert (
                result.stdout
                == '{\n    "session_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10",\n    "expires_at": "2022-06-21 16:40:00.634653+00:00",\n    "documentation_url": "https://docs.deepset.ai",\n    "ingestion_status": {\n        "failed_files": 0,\n        "finished_files": 1\n    }\n}\n'
            )


class TestCLIUtils:
    def test_login_with_minimal(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["login"], input="eu\ntest_api_key\n\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key\nAPI_URL=https://api.cloud.deepset.ai/api/v1\nDEFAULT_WORKSPACE_NAME=default"
                    == f.read()
                )

    def test_login_with_us_environment(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(cli_app, ["login"], input="us\ntest_api_key\nmy_workspace\n")
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key\nAPI_URL=http://api.us.deepset.ai/api/v1\nDEFAULT_WORKSPACE_NAME=my_workspace"
                    == f.read()
                )

    def test_login_with_custom_environment(self) -> None:
        fake_env_path = Path("./tests/tmp/.env")
        with patch("deepset_cloud_sdk.cli.ENV_FILE_PATH", fake_env_path):
            result = runner.invoke(
                cli_app, ["login"], input="custom\nhttps://custom-api.example.com\ntest_api_key\nmy_workspace\n"
            )
            assert result.exit_code == 0
            assert "created successfully" in result.stdout
            with open(fake_env_path) as f:
                assert (
                    "API_KEY=test_api_key\nAPI_URL=https://custom-api.example.com\nDEFAULT_WORKSPACE_NAME=my_workspace"
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
