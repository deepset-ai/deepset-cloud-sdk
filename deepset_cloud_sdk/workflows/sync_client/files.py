"""Sync client for files workflow."""
import asyncio
from pathlib import Path
from typing import Generator, List, Optional

import structlog

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.async_client.files import (
    list_files as async_list_files,
)
from deepset_cloud_sdk.workflows.async_client.files import upload as async_upload
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_file_paths as async_upload_file_paths,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_texts as async_upload_texts,
)
from deepset_cloud_sdk.workflows.sync_client.utils import iter_over_async

logger = structlog.get_logger(__name__)


def upload_file_paths(
    file_paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
    show_progress: bool = True,
) -> None:
    """Upload files to deepset Cloud.

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
            show_progress=show_progress,
        )
    )


def upload(
    paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
    show_progress: bool = True,
    recursive: bool = False,
) -> None:
    """Upload a folder to deepset Cloud.

    :param paths: Path to the folder to upload.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    asyncio.run(
        async_upload(
            paths=paths,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
            recursive=recursive,
        )
    )


def upload_texts(
    files: List[DeepsetCloudFile],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: int = 300,
    show_progress: bool = True,
) -> None:
    """Upload texts to deepset Cloud.

    :param files: List of DeepsetCloudFiles to upload.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    asyncio.run(
        async_upload_texts(
            files=files,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
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
) -> Generator[List[File], None, None]:
    """List files in deepset Cloud.

    WARNING: This only works for workspaces with up to 1000 files.

    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    :param batch_size: Batch size to use for the file list.
    :param timeout_s: Timeout in seconds for the API requests.
    """
    loop = asyncio.new_event_loop()

    async_list_files_generator = async_list_files(
        api_key=api_key,
        api_url=api_url,
        workspace_name=workspace_name,
        name=name,
        content=content,
        odata_filter=odata_filter,
        batch_size=batch_size,
        timeout_s=timeout_s,
    )
    try:
        yield from iter_over_async(async_list_files_generator, loop)
    finally:
        loop.close()
