# pylint:disable=too-many-arguments
"""This module contains async functions for uploading files and folders to deepset Cloud."""
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Union
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
from deepset_cloud_sdk._s3.upload import S3UploadSummary
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
    timeout_s: Optional[int] = None,
) -> AsyncGenerator[List[File], None]:
    """List all files in a workspace.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from. It uses the workspace from the .ENV file by default.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: The odata_filter to apply to the file list.
    For example, `odata_filter="category eq 'news'"` lists files with metadata `{"meta": {"category": "news"}}`.
    :param timeout_s: The timeout in seconds for this API call.
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
    timeout_s: Optional[int] = None,
) -> AsyncGenerator[List[UploadSessionDetail], None]:
    """List the details of all upload sessions for a given workspace, including the closed sessions.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from. It uses the workspace from the .ENV file by default.
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


async def upload(
    paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: Optional[int] = None,
    show_progress: bool = True,
    recursive: bool = False,
) -> S3UploadSummary:
    """Upload a folder to deepset Cloud.

    :param paths: Path to the folder to upload. If the folder contains unsupported files, they're skipped.
    during the upload. Supported file formats are TXT and PDF.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
    Possible options are:
    KEEP - uploads the file with the same name and keeps both files in the workspace.
    OVERWRITE - overwrites the file that is in the workspace.
    FAIL - fails to upload the file with the same name.
    :param blocking: Whether to wait for the upload to finish.
    :param timeout_s: Timeout in seconds for the upload.
    :param show_progress: Shows the upload progress.
    :param recursive: Uploads files from subdirectories as well.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        return await file_service.upload(
            workspace_name=workspace_name,
            paths=paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
            recursive=recursive,
        )


async def download(
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    file_dir: Optional[Union[Path, str]] = None,
    name: Optional[str] = None,
    content: Optional[str] = None,
    odata_filter: Optional[str] = None,
    include_meta: bool = True,
    batch_size: int = 50,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    show_progress: bool = True,
    timeout_s: Optional[int] = None,
) -> None:
    """Download a folder to deepset Cloud.

    Downloads all files from a workspace to a local folder.

    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param file_dir: Path to the folder to download. If the folder contains unsupported files, they're skipped.
    during the upload. Supported file formats are TXT and PDF.
    :param name: Name of the file to odata_filter by.
    :param content: Content of a file to odata_filter by.
    :param odata_filter: odata_filter by file meta data.
    :param include_meta: Whether to include the file meta in the folder.
    :param batch_size: Batch size for the listing.
    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param show_progress: Shows the upload progress.
    :param timeout_s: Timeout in seconds for the download.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        await file_service.download(
            workspace_name=workspace_name,
            file_dir=file_dir,
            name=name,
            content=content,
            odata_filter=odata_filter,
            include_meta=include_meta,
            batch_size=batch_size,
            show_progress=show_progress,
            timeout_s=timeout_s,
        )


async def upload_texts(
    files: List[DeepsetCloudFile],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    write_mode: WriteMode = WriteMode.KEEP,
    blocking: bool = True,
    timeout_s: Optional[int] = None,
    show_progress: bool = True,
) -> S3UploadSummary:
    """Upload raw texts to deepset Cloud.

    :param files: List of DeepsetCloudFiles to upload.
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
    :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
    Possible options are:
    KEEP - uploads the file with the same name and keeps both files in the workspace.
    OVERWRITE - overwrites the file that is in the workspace.
    FAIL - fails to upload the file with the same name.
    :param blocking: Whether to wait for the files to be listed and displayed in deepset Cloud.
    This may take a couple of minutes.
    :param timeout_s: Timeout in seconds for the `blocking` parameter.
    :param show_progress: Shows the upload progress.
    """
    async with FilesService.factory(_get_config(api_key=api_key, api_url=api_url)) as file_service:
        return await file_service.upload_texts(
            workspace_name=workspace_name,
            files=files,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
        )
