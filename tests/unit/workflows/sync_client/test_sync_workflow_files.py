import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, List, Optional
from unittest.mock import AsyncMock, patch
from uuid import UUID

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.sync_client.files import (
    list_files,
    upload_file_paths,
    upload_folder,
    upload_texts,
)


@patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_file_paths")
def test_upload_file_paths(async_file_upload_mock: AsyncMock) -> None:
    upload_file_paths(
        file_paths=[Path("./tests/data/example.txt")],
        write_mode=WriteMode.FAIL,
    )
    async_file_upload_mock.assert_called_once_with(
        file_paths=[Path("./tests/data/example.txt")],
        api_key=None,
        api_url=None,
        workspace_name=DEFAULT_WORKSPACE_NAME,
        write_mode=WriteMode.FAIL,
        blocking=True,
        timeout_s=300,
    )


@patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_folder")
def test_upload_folder(async_upload_folder_mock: AsyncMock) -> None:
    upload_folder(
        folder_path=Path("./tests/data/upload_folder"),
    )
    async_upload_folder_mock.assert_called_once_with(
        folder_path=Path("./tests/data/upload_folder"),
        api_key=None,
        api_url=None,
        workspace_name=DEFAULT_WORKSPACE_NAME,
        write_mode=WriteMode.KEEP,
        blocking=True,
        timeout_s=300,
    )


@patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_texts")
def test_upload_texts(async_upload_texts_mock: AsyncMock) -> None:
    dc_files = [
        DeepsetCloudFile(
            name="test_file.txt",
            text="test content",
            meta={"test": "test"},
        )
    ]
    upload_texts(dc_files=dc_files)
    async_upload_texts_mock.assert_called_once_with(
        dc_files=dc_files,
        api_key=None,
        api_url=None,
        workspace_name=DEFAULT_WORKSPACE_NAME,
        write_mode=WriteMode.KEEP,
        blocking=True,
        timeout_s=300,
    )


def test_list_files() -> None:
    async def mocked_async_list_files(*args: Any, **kwargs: Any) -> AsyncGenerator[List[File], None]:
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

    with patch("deepset_cloud_sdk.workflows.sync_client.files.async_list_files", new=mocked_async_list_files):
        file_list = list_files(
            workspace_name="my_workspace",
            name="test_file.txt",
            content="test content",
            filter="test",
            batch_size=100,
            timeout_s=100,
        )
        assert file_list == [
            File(
                file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                name="silly_things_1.txt",
                size=611,
                meta={},
                created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
            )
        ]
