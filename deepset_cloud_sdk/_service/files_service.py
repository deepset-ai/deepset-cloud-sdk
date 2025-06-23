"""Module for all file-related operations."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, Union
from uuid import UUID

import structlog
from tqdm import tqdm
from yaspin import yaspin
from yaspin.spinners import Spinners

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.files import (
    File,
    FileNotFoundInDeepsetCloudException,
    FilesAPI,
)
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSession,
    UploadSessionDetail,
    UploadSessionsAPI,
    UploadSessionStatus,
    WriteMode,
)
from deepset_cloud_sdk._s3.upload import S3, S3UploadResult, S3UploadSummary
from deepset_cloud_sdk.models import DeepsetCloudFileBase

logger = structlog.get_logger(__name__)

META_SUFFIX = ".meta.json"
DIRECT_UPLOAD_THRESHOLD = 20
DEFAULT_S3_CONCURRENCY = 10
DEFAULT_MAX_ATTEMPTS = 5
SAFE_MODE_CONCURRENCY = 1
SAFE_MODE_MAX_ATTEMPTS = 10


class FilesService:
    """Service for all file-related operations."""

    def __init__(self, upload_sessions: UploadSessionsAPI, files: FilesAPI, s3: S3):
        """Initialize the service.

        :param upload_sessions: API for upload sessions.
        :param files: API for files.
        :param s3: AWS S3 client.
        """
        self._upload_sessions = upload_sessions
        self._files = files
        self._s3 = s3

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[FilesService, None]:
        """Create a new instance of the service.

        :param config: CommonConfig object.
        :return: New instance of the service.
        """
        async with DeepsetCloudAPI.factory(config) as deepset_cloud_api:
            files_api = FilesAPI(deepset_cloud_api)
            upload_sessions_api = UploadSessionsAPI(deepset_cloud_api)
            concurrency = SAFE_MODE_CONCURRENCY if config.safe_mode else DEFAULT_S3_CONCURRENCY
            max_attempts = SAFE_MODE_MAX_ATTEMPTS if config.safe_mode else DEFAULT_MAX_ATTEMPTS
            async with S3(concurrency=concurrency, max_attempts=max_attempts) as s3:
                yield cls(upload_sessions_api, files_api, s3)

    async def _wait_for_finished(
        self,
        workspace_name: str,
        session_id: UUID,
        total_files: int,
        timeout_s: Optional[int] = None,
        show_progress: bool = True,
    ) -> None:
        start = time.time()
        ingested_files = 0
        pbar = None
        if show_progress:
            pbar = tqdm(total=total_files, desc="Ingestion Progress")

        while ingested_files < total_files:
            if timeout_s is not None and time.time() - start > timeout_s:
                raise TimeoutError("Ingestion timed out.")

            upload_session_status = await self._upload_sessions.status(
                workspace_name=workspace_name, session_id=session_id
            )
            ingested_files = (
                upload_session_status.ingestion_status.finished_files
                + upload_session_status.ingestion_status.failed_files
            )
            if pbar is not None:
                pbar.update(ingested_files - pbar.n)
            else:
                logger.info(
                    "Waiting for ingestion to finish.",
                    finished_files=upload_session_status.ingestion_status.finished_files,
                    failed_files=upload_session_status.ingestion_status.failed_files,
                    total_files=total_files,
                )
            await asyncio.sleep(2)

        if pbar is not None:
            pbar.close()

        if total_files > 0:
            logger.info(
                "Uploaded all files.",
                total_files=total_files,
                failed_files=upload_session_status.ingestion_status.failed_files,
            )

    @asynccontextmanager
    async def _create_upload_session(
        self,
        workspace_name: str,
        write_mode: WriteMode = WriteMode.KEEP,
        enable_parallel_processing: bool = False,
    ) -> AsyncGenerator[UploadSession, None]:
        """Create a new upload session.

        :param workspace_name: Name of the workspace to create the upload session for.
        :param enable_parallel_processing: If `True`, the deepset AI Platform ingests the files in parallel.
            Use this to speed up the upload process and if you are not running concurrent uploads for the same files.
        :return: Upload session ID.
        """
        upload_session = await self._upload_sessions.create(
            workspace_name=workspace_name, write_mode=write_mode, enable_parallel_processing=enable_parallel_processing
        )
        try:
            yield upload_session
        finally:
            await self._upload_sessions.close(workspace_name=workspace_name, session_id=upload_session.session_id)

    async def _wrapped_direct_upload_path(
        self, workspace_name: str, file_path: Path, meta: Dict[str, Any], write_mode: WriteMode
    ) -> S3UploadResult:
        try:
            await self._files.direct_upload_path(
                workspace_name=workspace_name,
                file_path=file_path,
                meta=meta,
                file_name=file_path.name,
                write_mode=write_mode,
            )
            logger.info("Successfully uploaded file.", file_path=file_path)
            return S3UploadResult(file_name=file_path.name, success=True)
        except Exception as error:
            logger.error("Failed uploading file.", file_path=file_path, error=error)
            return S3UploadResult(file_name=file_path.name, success=False, exception=error)

    async def _wrapped_direct_upload_in_memory(
        self,
        workspace_name: str,
        content: Union[str, bytes],
        file_name: str,
        meta: Dict[str, Any],
        write_mode: WriteMode,
    ) -> S3UploadResult:
        try:
            await self._files.direct_upload_in_memory(
                workspace_name=workspace_name,
                content=content,
                meta=meta,
                file_name=file_name,
                write_mode=write_mode,
            )
            logger.info("Successfully uploaded file.", file_name=file_name)
            return S3UploadResult(file_name=file_name, success=True)
        except Exception as error:
            logger.error("Failed uploading file.", file_name=file_name, error=error)
            return S3UploadResult(file_name=file_name, success=False, exception=error)

    async def upload_file_paths(
        self,
        workspace_name: str,
        file_paths: List[Path],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        show_progress: bool = True,
        timeout_s: Optional[int] = None,
        enable_parallel_processing: bool = False,
    ) -> S3UploadSummary:
        """Upload a list of files to a workspace.

        Upload a list of files to a selected workspace using upload sessions. It first uploads the files to S3 and then lists them in deepset AI Platform.
        Listing the files in deepset may take a couple of minutes. Use the `blocking` parameter to control if you want to wait until the files are listed and displayed in deepset AI Platform.
        If blocking is set to `True`, the function waits until all files are visible in deepset. If blocking is set to `False`, the function returns immediately after
        the upload of the files to S3 is completed and doesn't wait until the files are shown in deepset.

        :param workspace_name: Name of the workspace to upload the files to.
        :param file_paths: List of file paths to upload.
        :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
        Possible options are:
        KEEP - uploads the file with the same name and keeps both files in the workspace.
        OVERWRITE - overwrites the file that is in the workspace.
        FAIL - fails to upload the file with the same name.
        :param blocking: If True, waits until the ingestion is finished and the files are visible in deepset.
        :param timeout_s: Timeout in seconds for the `blocking` parameter.
        :param show_progress If True, shows a progress bar for S3 uploads.
        :param enable_parallel_processing: If `True`, the deepset will ingest the files in parallel.
            Use this to speed up the upload process and if you are not running concurrent uploads for the same files.

        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        if len(file_paths) <= DIRECT_UPLOAD_THRESHOLD:
            logger.info("Uploading files to deepset AI Platform.", file_paths=file_paths)
            _coroutines = []
            _raw_files = [path for path in file_paths if not path.name.endswith(META_SUFFIX)]
            for file_path in _raw_files:
                meta: Dict[str, Any] = {}
                meta_path = Path(str(file_path) + META_SUFFIX)
                if meta_path in file_paths:
                    with meta_path.open("r") as meta_file:
                        meta = json.loads(meta_file.read())

                _coroutines.append(
                    self._wrapped_direct_upload_path(
                        workspace_name=workspace_name, file_path=file_path, meta=meta, write_mode=write_mode
                    )
                )
            result = await asyncio.gather(*_coroutines)
            logger.info(
                "Finished uploading files.",
                number_of_successful_files=len(_raw_files),
                failed_files=[r for r in result if r.success is False],
            )
            return S3UploadSummary(
                total_files=len(_raw_files),
                successful_upload_count=len([r for r in result if r.success]),
                failed_upload_count=len([r for r in result if r.success is False]),
                failed=[r for r in result if r.success is False],
            )

        # create session to upload files to
        async with self._create_upload_session(
            workspace_name=workspace_name, write_mode=write_mode, enable_parallel_processing=enable_parallel_processing
        ) as upload_session:
            # upload file paths to session

            upload_summary = await self._s3.upload_files_from_paths(
                upload_session=upload_session, file_paths=file_paths, show_progress=show_progress
            )
            logger.info(
                "Summary of S3 Uploads",
                successful_uploads=upload_summary.successful_upload_count,
                failed_uploads=upload_summary.failed_upload_count,
                failed=upload_summary.failed,
            )

        # wait for ingestion to finish
        if blocking:
            total_files = len(list(filter(lambda x: not os.path.basename(x).endswith(META_SUFFIX), file_paths)))
            await self._wait_for_finished(
                workspace_name=workspace_name,
                session_id=upload_session.session_id,
                total_files=total_files,
                timeout_s=timeout_s,
                show_progress=show_progress,
            )
        return upload_summary

    @staticmethod
    def _get_file_paths(paths: List[Path], recursive: bool = False) -> List[Path]:
        """Get all valid file paths from a list of paths.

        Flatten a list of paths and return all valid file paths. If recursive is True, recursively walk through all
        subfolders and return all files.

        :param paths: List of paths to flatten.
        :param recursive: If True, recursively walk through all subfolders and return all files.
        """
        file_paths = []
        for path in paths:
            if path.is_file():
                file_paths.append(path)
            elif recursive:
                file_paths.extend([file_path for file_path in path.rglob("*") if file_path.is_file()])
            else:
                file_paths.extend([file_path for file_path in path.glob("*") if file_path.is_file()])
        return file_paths

    @staticmethod
    def _validate_file_paths(file_paths: List[Path]) -> None:
        """Validate a list of file paths.

        This method validates the file paths and raises a ValueError if the file paths are invalid.
        It also validates if there are metadata files mapped to not existing raw files.

        :param file_paths: A list of paths to upload.
        :raises ValueError: If the file paths are invalid.
        """
        logger.info("Validating file paths and metadata.")
        meta_file_names = list(
            map(
                lambda fp: os.path.basename(fp),
                [file_path for file_path in file_paths if str(file_path).endswith(META_SUFFIX)],
            )
        )
        file_names = list(map(lambda fp: os.path.basename(fp), file_paths))
        file_name_set = set(filter(lambda fn: not fn.endswith(META_SUFFIX), file_names))

        not_mapped_meta_files = [
            meta_file_name
            for meta_file_name in meta_file_names
            if meta_file_name.split(META_SUFFIX)[0] not in file_name_set
        ]

        if len(not_mapped_meta_files) > 0:
            raise ValueError(
                f"Metadata files without corresponding files were found: {not_mapped_meta_files}. "
                "Make sure each metadata file has a corresponding file. "
                "Map the files using file names like this: '<file_name>' and '<file_name>.meta.json'. "
                "For example: 'file1.txt' and 'file1.txt.meta.json'."
            )

    @staticmethod
    def _remove_duplicates(file_paths: List[Path]) -> List[Path]:
        # Group files by their names
        files_by_name = defaultdict(list)
        for file_path in file_paths:
            files_by_name[file_path.name].append(file_path)

        # For each group, sort by modification time and select the most recent
        most_recent_files = []
        for file_name, file_group in files_by_name.items():
            if len(file_group) > 1:
                logger.warning(
                    "Multiple files with the same name found. Keeping the most recent one.", file_name=file_name
                )
            most_recent_file = sorted(file_group, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            most_recent_files.append(most_recent_file)

        return most_recent_files

    @staticmethod
    def _preprocess_paths(
        paths: List[Path],
        spinner: Spinners = None,
        recursive: bool = False,
        desired_file_types: List[str] | None = None,
    ) -> List[Path]:
        all_files = FilesService._get_file_paths(paths, recursive=recursive)

        file_paths = [path for path in all_files if path.is_file() and not str(path).endswith(META_SUFFIX)]
        if desired_file_types is not None:
            file_paths = [path for path in file_paths if path.suffix in desired_file_types]

        meta_file_path = [path for path in all_files if path.is_file() and str(path).endswith(".meta.json")]
        if desired_file_types is not None:
            meta_file_path = [
                path
                for path in meta_file_path
                if str(path).endswith(tuple(f"{file_type}.meta.json" for file_type in desired_file_types))
            ]
        combined_paths = meta_file_path + file_paths

        combined_paths = FilesService._remove_duplicates(combined_paths)
        if len(combined_paths) < len(all_files):
            logger.warning(
                "Skipping files with unsupported file format.",
                paths=paths,
                skipped_files=len(all_files) - len(combined_paths),
            )
            for skipped_file in set(all_files) - set(combined_paths):
                logger.warning("Skipping file", file_path=skipped_file)

        if spinner is not None:
            spinner.text = "Validating files and metadata."
        FilesService._validate_file_paths(combined_paths)

        return combined_paths

    async def upload(
        self,
        workspace_name: str,
        paths: List[Path],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: Optional[int] = None,
        show_progress: bool = True,
        recursive: bool = False,
        desired_file_types: Optional[List[str]] = None,
        enable_parallel_processing: bool = False,
    ) -> S3UploadSummary:
        """Upload a list of file or folder paths to a workspace.

        Upload files to a selected workspace using upload sessions. It first uploads the files to S3 and then lists them in deepset AI Platform.
        Listing the files in deepset may take a couple of minutes. Use the `blocking` parameter to control if you want to wait until the files are listed and displayed in deepset.
        If blocking is set to `True`, the function waits until all files are visible in deepset. If blocking is set to `False`, the function returns immediately after
        the upload of the files to S3 is completed and doesn't wait until the files are shown in deepset.

        :param workspace_name: Name of the workspace to upload the files to.
        :param paths: Path to the folder to upload.
        :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
        Possible options are:
        KEEP - uploads the file with the same name and keeps both files in the workspace.
        OVERWRITE - overwrites the file that is in the workspace.
        FAIL - fails to upload the file with the same name.
        :param blocking: If True, waits until the ingestion to S3 is finished and the files are visible in deepset AI Platform.
        :param timeout_s: Timeout in seconds for the `blocking` parameter.
        :param show_progress If True, shows a progress bar for S3 uploads.
        :param recursive: If True, recursively uploads all files in the folder.
        :param desired_file_types: A list of allowed file types to upload, defaults to
        `[".txt", ".pdf", ".docx", ".pptx", ".xlsx", ".xml", ".csv", ".html", ".md", ".json"]`
        :param enable_parallel_processing: If `True`, the deepset AI Platform ingests the files in parallel.
            Use this to speed up the upload process and if you are not running concurrent uploads for the same files.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        logger.info("Getting valid files from file path. This may take a few minutes.", recursive=recursive)

        if show_progress:
            with yaspin().arc as sp:
                sp.text = "Finding uploadable files in the given paths."
                file_paths = self._preprocess_paths(
                    paths, spinner=sp, recursive=recursive, desired_file_types=desired_file_types
                )
        else:
            file_paths = self._preprocess_paths(paths, recursive=recursive, desired_file_types=desired_file_types)

        return await self.upload_file_paths(
            workspace_name=workspace_name,
            file_paths=file_paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
            enable_parallel_processing=enable_parallel_processing,
        )

    async def _download_and_log_errors(
        self,
        workspace_name: str,
        file_id: UUID,
        file_name: str,
        file_dir: Optional[Union[Path, str]],
        include_meta: bool,
    ) -> None:
        try:
            await self._files.download(
                workspace_name=workspace_name,
                file_id=file_id,
                file_name=file_name,
                file_dir=file_dir,
                include_meta=include_meta,
            )
        except FileNotFoundInDeepsetCloudException as e:
            logger.error(
                "File was listed in deepset AI Platform but could not be downloaded.", file_id=file_id, error=e
            )
        except Exception as e:
            logger.error("Failed to download file.", file_id=file_id, error=e)

    async def download(
        self,
        workspace_name: str,
        file_dir: Optional[Union[Path, str]] = None,
        name: Optional[str] = None,
        odata_filter: Optional[str] = None,
        include_meta: bool = True,
        batch_size: int = 50,
        timeout_s: Optional[int] = None,
        show_progress: bool = True,
    ) -> None:
        """Download files from deepset AI Platform to a folder.

        :param workspace_name: Name of the workspace to upload the files to. It uses the workspace from the .ENV file by default.
        :param file_dir: Path to the folder to download. If None, the current working directory is used.
        :param name: odata_filter by file name.
        :param odata_filter: odata_filter by file meta data.
        :param include_meta: If True, downloads the metadata files as well.
        :param batch_size: Batch size for the listing.
        :param timeout_s: Timeout in seconds for the download.
        :param show_progress: Shows the upload progress.
        """
        start = time.time()
        logger.info("Start downloading files.", workspace_name=workspace_name)

        pbar: Optional[tqdm] = None
        if show_progress:
            total = (
                await self._files.list_paginated(
                    workspace_name,
                    name=name,
                    odata_filter=odata_filter,
                    limit=1,
                )
            ).total
            pbar = tqdm(total=total, desc="Download Progress")

        after_value = None
        after_file_id = None
        has_more: bool = True
        try:
            while has_more:
                if timeout_s is not None and time.time() - start > timeout_s:
                    raise TimeoutError("Download timed out.")

                response = await self._files.list_paginated(
                    workspace_name=workspace_name,
                    name=name,
                    odata_filter=odata_filter,
                    limit=batch_size,
                    after_file_id=after_file_id,
                    after_value=after_value,
                )
                has_more = response.has_more
                if not response.data:
                    return

                after_value = response.data[-1].created_at
                after_file_id = response.data[-1].file_id

                await asyncio.gather(
                    *[
                        self._download_and_log_errors(
                            workspace_name=workspace_name,
                            file_id=_file.file_id,
                            file_name=_file.name,
                            file_dir=file_dir,
                            include_meta=include_meta,
                        )
                        for _file in response.data
                    ]
                )
                if pbar is not None:
                    pbar.update(batch_size)
        finally:
            if pbar is not None:
                pbar.close()

    async def upload_in_memory(
        self,
        workspace_name: str,
        files: Sequence[DeepsetCloudFileBase],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: Optional[int] = None,
        show_progress: bool = True,
        enable_parallel_processing: bool = False,
    ) -> S3UploadSummary:  # noqa
        """
        Upload a list of raw texts to a workspace using upload sessions. This method accepts a list of DeepsetCloudFiles
        which contain raw text, file name, and optional metadata.

        It first uploads the files to S3 and then lists them in deepset AI Platform.
        Listing the files in deepset may take a couple of minutes. Use the `blocking` parameter to control if you want to wait until the files are listed and displayed in deepset.
        If blocking is set to `True`, the function waits until all files are visible in deepset. If blocking is set to `False`, the function returns immediately after
        the upload of the files to S3 is completed and doesn't wait until the files are shown in deepset.

        :param workspace_name: Name of the workspace to upload the files to.
        :param files: List of DeepsetCloudFiles to upload.
        :param write_mode: Specifies what to do when a file with the same name already exists in the workspace.
        Possible options are:
        KEEP - uploads the file with the same name and keeps both files in the workspace.
        OVERWRITE - overwrites the file that is in the workspace.
        FAIL - fails to upload the file with the same name.
        :param enable_parallel_processing: If `True`, the deepset AI Platform ingests the files in parallel.
            Use this to speed up the upload process and if you are not running concurrent uploads for the same files.
        :param blocking: If True, waits until the ingestion to S3 is finished and the files are displayed in deepset AI Platform.
        :param timeout_s: Timeout in seconds for the `blocking` parameter.
        :param show_progress If True, shows a progress bar for S3 uploads.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        if len(files) <= DIRECT_UPLOAD_THRESHOLD:
            logger.info("Uploading files to deepset AI Platform.", total_text_files=len(files))
            _coroutines = []
            for file in files:
                _coroutines.append(
                    self._wrapped_direct_upload_in_memory(
                        workspace_name=workspace_name,
                        file_name=file.name,
                        meta=file.meta or {},
                        content=file.content(),
                        write_mode=write_mode,
                    )
                )
            result = await asyncio.gather(*_coroutines)
            logger.info(
                "Finished uploading files.",
                number_of_successful_files=len(files),
                failed_files=[r for r in result if r.success is False],
            )
            return S3UploadSummary(
                total_files=len(files),
                successful_upload_count=len([r for r in result if r.success]),
                failed_upload_count=len([r for r in result if r.success is False]),
                failed=[r for r in result if r.success is False],
            )

        # create session to upload files to
        async with self._create_upload_session(
            workspace_name=workspace_name, write_mode=write_mode, enable_parallel_processing=enable_parallel_processing
        ) as upload_session:
            upload_summary = await self._s3.upload_in_memory(
                upload_session=upload_session, files=files, show_progress=show_progress
            )

            logger.info(
                "Summary of S3 Uploads",
                successful_uploads=upload_summary.successful_upload_count,
                failed_uploads=upload_summary.failed_upload_count,
                failed=upload_summary.failed,
            )

        if blocking:
            await self._wait_for_finished(
                workspace_name=workspace_name,
                session_id=upload_session.session_id,
                total_files=len(files),
                timeout_s=timeout_s,
                show_progress=show_progress,
            )
        return upload_summary

    async def list_all(
        self,
        workspace_name: str,
        name: Optional[str] = None,
        odata_filter: Optional[str] = None,
        batch_size: int = 100,
        timeout_s: Optional[int] = None,
    ) -> AsyncGenerator[List[File], None]:
        """List all files in a workspace.

        Returns an async generator that yields lists of files. The generator is finished when all files are listed.
        You can specify the batch size per number of returned files using `batch_size`.

        :param workspace_name: Name of the workspace whose files you want to list.
        :param name: odata_filter by file name.
        :param odata_filter: odata_filter by file meta data.
        :param batch_size: Number of files to return per request.
        :param timeout_s: Timeout in seconds for the listing.
        :raises TimeoutError: If the listing takes longer than timeout_s.
        """
        start = time.time()
        has_more = True

        after_value = None
        after_file_id = None
        while has_more:
            if timeout_s is not None and time.time() - start > timeout_s:
                raise TimeoutError(f"Listing all files in workspace {workspace_name} timed out.")
            response = await self._files.list_paginated(
                workspace_name,
                name=name,
                odata_filter=odata_filter,
                limit=batch_size,
                after_file_id=after_file_id,
                after_value=after_value,
            )
            has_more = response.has_more
            if not response.data:
                return
            after_value = response.data[-1].created_at
            after_file_id = response.data[-1].file_id
            yield response.data

    async def list_upload_sessions(
        self,
        workspace_name: str,
        is_expired: Optional[bool] = False,
        batch_size: int = 100,
        timeout_s: Optional[int] = None,
    ) -> AsyncGenerator[List[UploadSessionDetail], None]:  # noqa: F821
        """List all upload sessions files in a workspace.

        Returns an async generator that yields lists of files. The generator is finished when all files are listed.
        You can specify the batch size per number of returned files using `batch_size`.

        :param workspace_name: Name of the workspace whose files you want to list.
        :param is_expired: Whether to list expired upload sessions.
        :param batch_size: Number of files to return per request.
        :param timeout_s: Timeout in seconds for the listing.
        :raises TimeoutError: If the listing takes longer than timeout_s.
        """
        start = time.time()
        has_more = True

        page_number: int = 1
        while has_more:
            if timeout_s is not None and time.time() - start > timeout_s:
                raise TimeoutError(f"Listing all upload sessions files in workspace {workspace_name} timed out.")
            response = await self._upload_sessions.list(
                workspace_name,
                is_expired=is_expired,
                limit=batch_size,
                page_number=page_number,
            )
            has_more = response.has_more
            if not response.data:
                return

            page_number += 1
            yield response.data

    async def get_upload_session(self, workspace_name: str, session_id: UUID) -> UploadSessionStatus:
        """Get the status of an upload session.

        :param workspace_name: Name of the workspace whose upload session you want to get.
        :param session_id: ID of the upload session.
        :return: UploadSessionStatus object.
        """
        upload_session_status: UploadSessionStatus = await self._upload_sessions.status(
            workspace_name=workspace_name, session_id=session_id
        )
        return upload_session_status
