import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, List
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from _pytest.monkeypatch import MonkeyPatch
from sniffio import AsyncLibraryNotFoundError

from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSessionDetail,
    UploadSessionStatusEnum,
    UploadSessionWriteModeEnum,
    WriteMode,
)
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile, FilesService
from deepset_cloud_sdk.models import UserInfo
from deepset_cloud_sdk.workflows.async_client.files import (
    list_files,
    list_upload_sessions,
    upload,
    upload_file_paths,
    upload_texts,
)


@pytest.mark.asyncio
class TestUploadFiles:
    async def test_upload_file_paths(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload_file_paths = AsyncMock(return_value=None)

        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
        await upload_file_paths(
            file_paths=[Path("./tests/data/example.txt")], write_mode=WriteMode.OVERWRITE, show_progress=False
        )

        mocked_upload_file_paths.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            file_paths=[Path("./tests/data/example.txt")],
            write_mode=WriteMode.OVERWRITE,
            blocking=True,
            timeout_s=300,
            show_progress=False,
        )

    async def test_upload_show_progress(self, monkeypatch: MonkeyPatch) -> None:
        paths = [Path("./tests/data/example.txt")]
        mocked_preprocess = AsyncMock(return_value=paths)
        mocked_upload_file_paths = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "_preprocess_paths", mocked_preprocess)
        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)

        await upload(paths=paths, show_progress=True)

        assert mocked_preprocess.call_args.kwargs.get("spinner") is not None

    async def test_upload_dont_show_progress(self, monkeypatch: MonkeyPatch) -> None:
        paths = [Path("./tests/data/example.txt")]
        mocked_preprocess = AsyncMock(return_value=paths)
        mocked_upload_file_paths = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "_preprocess_paths", mocked_preprocess)
        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)

        await upload(paths=paths, show_progress=False)

        assert mocked_preprocess.call_args.kwargs.get("spinner") is None

    async def test_upload(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload = AsyncMock(return_value=None)

        monkeypatch.setattr(FilesService, "upload", mocked_upload)
        await upload(paths=[Path("./tests/data/upload_folder")])

        mocked_upload.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            paths=[Path("./tests/data/upload_folder")],
            write_mode=WriteMode.KEEP,
            blocking=True,
            timeout_s=300,
            show_progress=True,
            recursive=False,
        )

    async def test_upload_texts(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload_texts = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "upload_texts", mocked_upload_texts)
        files = [
            DeepsetCloudFile(
                name="test_file.txt",
                text="test content",
                meta={"test": "test"},
            )
        ]
        await upload_texts(files=files)

        mocked_upload_texts.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            files=files,
            write_mode=WriteMode.KEEP,
            blocking=True,
            timeout_s=300,
            show_progress=True,
        )


@pytest.mark.asyncio
class TestListFiles:
    async def test_list_files(self, monkeypatch: MonkeyPatch) -> None:
        async def mocked_list_all(
            self: Any,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncGenerator[List[File], None]:
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

        monkeypatch.setattr(FilesService, "list_all", mocked_list_all)
        async for file_batch in list_files(
            workspace_name="my_workspace",
            name="test_file.txt",
            content="test content",
            odata_filter="test",
            batch_size=100,
            timeout_s=100,
        ):
            assert file_batch == [
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ]

    async def test_list_files_silence_exit(self, monkeypatch: MonkeyPatch) -> None:
        async def mocked_list_all(
            self: Any,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncGenerator[List[File], None]:
            raise AsyncLibraryNotFoundError()
            yield []  # for some reason monkeypatch requires to have the yield statement

        monkeypatch.setattr(FilesService, "list_all", mocked_list_all)
        async for file_batch in list_files(
            workspace_name="my_workspace",
            name="test_file.txt",
            content="test content",
            odata_filter="test",
            batch_size=100,
            timeout_s=100,
        ):
            pass


@pytest.mark.asyncio
class TestListUploadSessions:
    async def test_list_upload_sessions(self, monkeypatch: MonkeyPatch) -> None:
        async def mocked_list_upload_sessions(
            self: Any,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncGenerator[List[File], None]:
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
                    status=UploadSessionStatusEnum.CLOSED,
                )
            ]

        monkeypatch.setattr(FilesService, "list_upload_sessions", mocked_list_upload_sessions)
        async for upload_session_batch in list_upload_sessions(
            workspace_name="my_workspace",
            is_expired=False,
            batch_size=100,
            timeout_s=100,
        ):
            assert upload_session_batch == [
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
                    status=UploadSessionStatusEnum.CLOSED,
                )
            ]

    async def test_list_files_silence_exit(self, monkeypatch: MonkeyPatch) -> None:
        async def mocked_list_upload_sessions(
            self: Any,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncGenerator[List[File], None]:
            raise AsyncLibraryNotFoundError()
            yield []  # for some reason monkeypatch requires to have the yield statement

        monkeypatch.setattr(FilesService, "list_upload_sessions", mocked_list_upload_sessions)
        async for _ in list_upload_sessions(
            workspace_name="my_workspace",
            batch_size=100,
            timeout_s=100,
        ):
            pass
