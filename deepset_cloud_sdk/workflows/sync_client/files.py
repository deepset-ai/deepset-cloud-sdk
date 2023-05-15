# pylint: disable=too-many-arguments
"""Sync client for files workflow."""
import asyncio
from pathlib import Path
from typing import List, Optional

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.async_client.files import (
    list_files as async_list_files,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_file_paths as async_upload_file_paths,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_folder as async_upload_folder,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_texts as async_upload_texts,
)


def upload_file_paths(
    file_paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    """Upload files to the Deepset Cloud.

    :param file_paths: List of file paths to upload.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    asyncio.run(
        async_upload_file_paths(
            file_paths=file_paths,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
        )
    )


def upload_folder(
    folder_path: Path,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    """Upload a folder to the Deepset Cloud.

    :param folder_path: Path to the folder to upload.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    asyncio.run(
        async_upload_folder(
            folder_path=folder_path,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
        )
    )


def upload_texts(
    dc_files: List[DeepsetCloudFile],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    """Upload texts to the Deepset Cloud.

    :param dc_files: List of DeepsetCloudFiles to upload.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    asyncio.run(
        async_upload_texts(
            dc_files=dc_files,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
        )
    )


def list_files(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    name: Optional[str] = None,
    content: Optional[str] = None,
    odata_filter: Optional[str] = None,
    batch_size: int = 100,
    timeout_s: int = 300,
) -> List[File]:
    """List files in the Deepset Cloud.

    WARNING: this will only work for workspaces up to 1000 files.
    TODO: make this a generator

    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    :param batch_size: Batch size to use for the file list.
    """

    async def list_files_async() -> List[File]:
        files: List[File] = []
        async for file_batch in async_list_files(
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            name=name,
            content=content,
            odata_filter=odata_filter,
            batch_size=batch_size,
            timeout_s=timeout_s,
        ):
            files += file_batch
        return files

    return asyncio.run(list_files_async())
