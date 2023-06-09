# pylint:disable=too-many-arguments
"""This module contains async functions for uploading files and folders to deepset Cloud."""
from pathlib import Path
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sniffio import AsyncLibraryNotFoundError

from deepset_cloud_sdk._api.config import (
    API_KEY,
    API_URL,
    DEFAULT_WORKSPACE_NAME,
    CommonConfig,
)
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSessionDetail,
    UploadSessionStatus,
    WriteMode,
)
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile, FilesService


def _get_config(api_key: Optional[str] = None, api_url: Optional[str] = None) -> CommonConfig:
    return CommonConfig(api_key=api_key or API_KEY, api_url=api_url or API_URL)


async def list_files(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    name: Optional[str] = None,
    content: Optional[str] = None,
    odata_filter: Optional[str] = None,
    batch_size: int = 100,
    timeout_s: int = 300,
) -> AsyncGenerator[List[File], None]:
    """List all files in a workspace.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param batch_size: Batch size for the listing.
    :return: List of files.
    """
    try:
        async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                name=name,
                content=content,
                odata_filter=odata_filter,
                batch_size=batch_size,
                timeout_s=timeout_s,
            ):
                yield file_batch
    except AsyncLibraryNotFoundError:
        # since we are using asyncio.run() in the sync wrapper, we need to catch this error
        pass


async def list_upload_sessions(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    is_expired: Optional[bool] = None,
    batch_size: int = 100,
    timeout_s: int = 300,
) -> AsyncGenerator[List[UploadSessionDetail], None]:
    """List all files in a workspace.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param is_expired: Whether to list expired upload sessions.
    :param batch_size: Batch size for the listing.
    :param timeout_s: Timeout in seconds for the API requests.
    :return: List of files.
    """
    try:
        async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
            async for upload_session_batch in file_service.list_upload_sessions(
                workspace_name=workspace_name,
                is_expired=is_expired,
                batch_size=batch_size,
                timeout_s=timeout_s,
            ):
                yield upload_session_batch
    except AsyncLibraryNotFoundError:
        # since we are using asyncio.run() in the sync wrapper, we need to catch this error
        pass


async def get_upload_session(
    session_id: UUID,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
) -> UploadSessionStatus:
    """Get the status of an upload session.

    :param session_id: ID of the upload session to get the status for.
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :return: List of files.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        return await file_service.get_upload_session(
            workspace_name=workspace_name,
            session_id=session_id,
        )


async def upload_file_paths(
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
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        await file_service.upload_file_paths(
            workspace_name=workspace_name,
            file_paths=file_paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
        )


async def upload(
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

    :param paths: Path to the folder to upload. If the folder contains unsupported files, they're skipped
    during the upload. Supported file formats are TXT and PDF.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        await file_service.upload(
            workspace_name=workspace_name,
            paths=paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
            recursive=recursive,
        )


async def upload_texts(
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
    :param workspace_name: Name of the workspace to upload the files to.
    :param blocking: Whether to wait for the files to be listed and displayed in deepset Cloud.
    This may take a couple of minutes.
    :param timeout_s: Timeout in seconds for the `blocking` parameter.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        await file_service.upload_texts(
            workspace_name=workspace_name,
            files=files,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
        )
