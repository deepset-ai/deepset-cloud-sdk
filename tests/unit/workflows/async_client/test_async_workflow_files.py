from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.service.files_service import DeepsetCloudFiles, FilesService
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_file_paths,
    upload_folder,
    upload_texts,
)


@pytest.mark.asyncio
class TestUploadFiles:
    async def test_upload_file_paths(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload_file_paths = AsyncMock(return_value=None)

        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
        await upload_file_paths(file_paths=[Path("./tests/data/example.txt")])

        mocked_upload_file_paths.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            file_paths=[Path("./tests/data/example.txt")],
            blocking=True,
            timeout_s=300,
        )

    async def test_upload_folder(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload_folder = AsyncMock(return_value=None)

        monkeypatch.setattr(FilesService, "upload_folder", mocked_upload_folder)
        await upload_folder(folder_path=Path("./tests/data/upload_folder"))

        mocked_upload_folder.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            folder_path=Path("./tests/data/upload_folder"),
            blocking=True,
            timeout_s=300,
        )

    async def test_upload_texts(self, monkeypatch: MonkeyPatch) -> None:
        mocked_upload_texts = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "upload_texts", mocked_upload_texts)
        dc_files = [
            DeepsetCloudFiles(
                name="test_file.txt",
                text="test content",
                meta={"test": "test"},
            )
        ]
        await upload_texts(dc_files=dc_files)

        mocked_upload_texts.assert_called_once_with(
            workspace_name=DEFAULT_WORKSPACE_NAME,
            dc_files=dc_files,
            blocking=True,
            timeout_s=300,
        )
