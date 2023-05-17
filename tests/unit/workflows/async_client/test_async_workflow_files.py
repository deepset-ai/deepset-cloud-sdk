import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, List, Optional
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from _pytest.monkeypatch import MonkeyPatch
from sniffio import AsyncLibraryNotFoundError

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile, FilesService
from deepset_cloud_sdk.workflows.async_client.files import (
    list_files,
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
