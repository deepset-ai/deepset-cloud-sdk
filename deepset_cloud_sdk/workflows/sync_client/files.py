"""Sync client for files workflow."""
import asyncio
from pathlib import Path
from typing import Generator, List, Optional
from uuid import UUID

import structlog

from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSessionDetail,
    UploadSessionStatus,
    WriteMode,
)
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.async_client.files import (
    get_upload_session as async_get_upload_session,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    list_files as async_list_files,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    list_upload_sessions as async_list_upload_sessions,
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
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param write_mode: The write mode determines how to handle uploading a file if it's already in the workspace.
        Your options are: keep the file with the same name, make the request fail if a file with the same name already
        exists, or overwrite the file. If you choose to overwrite, all files with the same name are overwritten.
    :param blocking: Whether to wait for the files to be uploaded and listed in deepset Cloud.
    :param timeout_s: Timeout in seconds for the `blocking` parameter`.
    :param show_progress: Shows the upload progress.
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

    :param paths: Path to the folder to upload. If the folder contains unsupported file types, they're skipped.
    deepset Cloud supports TXT and PDF files.
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param write_mode: The write mode determines how to handle uploading a file if it's already in the workspace.
        Your options are: keep the file with the same name, make the request fail if a file with the same name already
        exists, or overwrite the file. If you choose to overwrite, all files with the same name are overwritten.
    :param blocking: Whether to wait for the files to be uploaded and displayed in deepset Cloud.
    :param timeout_s: Timeout in seconds for the `blocking` parameter.
    :param show_progress: Shows the upload progress.
    :param recursive: Uploads files from subfolders as well.
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
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
    Possible options are:
    KEEP - uploads the file with the same name and keeps both files in the workspace.
    OVERWRITE - overwrites the file that is in the workspace.
    FAIL - fails to upload the file with the same name.
    :param blocking: Whether to wait for the files to be uploaded and listed in deepset Cloud.
    :param timeout_s: Timeout in seconds for the `blocking` parameter.
    :param show_progress: Shows the upload progress.
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


def get_upload_session(
    session_id: UUID,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
) -> UploadSessionStatus:
    """Get the status of an upload session.

    :param session_id: ID of the upload session to get the status for.
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    """
    return asyncio.run(
        async_get_upload_session(session_id=session_id, api_key=api_key, api_url=api_url, workspace_name=workspace_name)
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
    """List files in a deepset Cloud workspace.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from. It uses the workspace from the .ENV file by default.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    For example, `odata_filter="category eq 'news'" lists files with metadata `{"meta": {"category": "news"}}.
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


def list_upload_sessions(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    is_expired: Optional[bool] = False,
    batch_size: int = 100,
    timeout_s: int = 300,
) -> Generator[List[UploadSessionDetail], None, None]:
    """List the details of all upload sessions, including the closed ones.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace whose sessions you want to list. It uses the workspace from the .ENV file by default.
    :param is_expired: Lists expired sessions.
    :param batch_size: Batch size to use for the session list.
    :param timeout_s: Timeout in seconds for the API request.
    """
    loop = asyncio.new_event_loop()

    async_list_files_generator = async_list_upload_sessions(
        api_key=api_key,
        api_url=api_url,
        workspace_name=workspace_name,
        is_expired=is_expired,
        batch_size=batch_size,
        timeout_s=timeout_s,
    )
    try:
        yield from iter_over_async(async_list_files_generator, loop)
    finally:
        loop.close()
