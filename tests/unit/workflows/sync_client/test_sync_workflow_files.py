from pathlib import Path
from typing import List, Optional
from unittest.mock import AsyncMock, patch

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.workflows.sync_client.files import (
    upload_file_paths,
    upload_folder,
)


@patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_file_paths")  # , new=async_upload_file_paths)
def test_upload_file_paths(async_file_upload_mock: AsyncMock) -> None:
    upload_file_paths(
        file_paths=[Path("./tests/data/example.txt")],
    )
    async_file_upload_mock.assert_called_once_with(
        file_paths=[Path("./tests/data/example.txt")],
        api_key=None,
        api_url=None,
        workspace_name=DEFAULT_WORKSPACE_NAME,
        blocking=True,
        timeout_s=300,
    )


@patch("deepset_cloud_sdk.workflows.sync_client.files.async_upload_folder")  # , new=async_upload_file_paths)
def test_upload_folder(async_upload_folder_mock: AsyncMock) -> None:
    upload_folder(
        folder_path=Path("./tests/data/upload_folder"),
    )
    async_upload_folder_mock.assert_called_once_with(
        folder_path=Path("./tests/data/upload_folder"),
        api_key=None,
        api_url=None,
        workspace_name=DEFAULT_WORKSPACE_NAME,
        blocking=True,
        timeout_s=300,
    )
