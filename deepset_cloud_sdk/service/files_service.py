"""Module for all file-related operations."""
from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List, Optional
from uuid import UUID

import structlog
from tqdm import tqdm
from yaspin import yaspin

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.api.files import File, FilesAPI
from deepset_cloud_sdk.api.upload_sessions import (
    UploadSession,
    UploadSessionsAPI,
    WriteMode,
)
from deepset_cloud_sdk.models import DeepsetCloudFile
from deepset_cloud_sdk.s3.upload import S3

logger = structlog.get_logger(__name__)


class FilesService:
    """Service for all file-related operations."""

    def __init__(self, upload_sessions: UploadSessionsAPI, files: FilesAPI, s3: S3):
        """Initialize the service.

        :param upload_sessions: API for upload sessions.
        :param files: API for files.
        :param aws: AWS client.
        """
        self._upload_sessions = upload_sessions
        self._files = files
        self._s3 = s3

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[FilesService, None]:
        """Create a new instance of the service.

        :param config: CommonConfig object.
        :param client: httpx client.
        :return: New instance of the service.
        """
        async with DeepsetCloudAPI.factory(config) as deepset_cloud_api:
            files_api = FilesAPI(deepset_cloud_api)
            upload_sessions_api = UploadSessionsAPI(deepset_cloud_api)

            yield cls(upload_sessions_api, files_api, S3(concurrency=30))

    async def _wait_for_finished(
        self, workspace_name: str, session_id: UUID, total_files: int, timeout_s: int, show_progress: bool = True
    ) -> None:
        start = time.time()
        ingested_files = 0
        pbar = None
        if show_progress:
            pbar = tqdm(total=total_files, desc="Ingestion Progress")

        while ingested_files < total_files:
            if time.time() - start > timeout_s:
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

        logger.warning(
            "Listing the files in deepset Cloud can still take up to 3 minutes after marking them as finished."
        )

    @asynccontextmanager
    async def _create_upload_session(
        self,
        workspace_name: str,
        write_mode: WriteMode = WriteMode.KEEP,
    ) -> AsyncGenerator[UploadSession, None]:
        """Create a new upload session.

        :param workspace_name: Name of the workspace to create the upload session for.
        :return: Upload session id.
        """
        upload_session = await self._upload_sessions.create(workspace_name=workspace_name, write_mode=write_mode)
        try:
            yield upload_session
        finally:
            await self._upload_sessions.close(workspace_name=workspace_name, session_id=upload_session.session_id)

    async def upload_file_paths(
        self,
        workspace_name: str,
        file_paths: List[Path],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: int = 300,
        show_progress: bool = True,
    ) -> None:
        """Upload a list of files to a workspace.

        Upload a list of files  to a selected workspace using upload sessions. If blocking is True, the function waits until
        all files are uploaded and listed by deepset Cloud. If blocking is False, the function returns immediately after
        the upload of the files is done. Note: It can take a while until the files are listed in deepset Cloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :file_paths: List of file paths to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :show_progress If True, shows a progress bar for S3 uploads
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        # create session to upload files to
        async with self._create_upload_session(workspace_name=workspace_name, write_mode=write_mode) as upload_session:
            # upload file paths to session

            upload_summary = await self._s3.upload_files_from_paths(
                upload_session=upload_session, file_paths=file_paths
            )
            logger.info(
                "Summary of S3 Uploads",
                successful_uploads=upload_summary.successful_upload_count,
                failed_uploads=upload_summary.failed_upload_count,
                failed=upload_summary.failed,
            )

        # wait for ingestion to finish
        if blocking:
            total_files = len(list(filter(lambda x: not os.path.basename(x).endswith(".meta.json"), file_paths)))
            await self._wait_for_finished(
                workspace_name=workspace_name,
                session_id=upload_session.session_id,
                total_files=total_files,
                timeout_s=timeout_s,
                show_progress=show_progress,
            )

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
                file_paths.extend([file_path for file_path in path.rglob("*")])
            else:
                file_paths.extend([file_path for file_path in path.glob("*")])
        return file_paths

    @staticmethod
    def _validate_file_paths(file_paths: List[Path]) -> None:
        """Validate a list of file paths.

        This method validates the file paths and raises a ValueError if the file paths are invalid.
        It also validates if there are meta files mapped to not existing raw files.

        :param file_paths: A list of paths to upload.
        :raises ValueError: If the file paths are invalid.
        """
        logger.info("Validating file paths and metadata")
        allowed_suffixes = {".txt", ".json", ".pdf"}
        for file_path in file_paths:
            if not file_path.suffix.lower() in allowed_suffixes:
                raise ValueError(f"Invalid file extension: {file_path.suffix}")
            if file_path.suffix.lower() == ".json" and not str(file_path).endswith(".meta.json"):
                raise ValueError(
                    f"JSON files are only supported for meta files. Please make sure to name your files '<file_name>.meta.json'. Got {file_path.name}."
                )
        meta_file_names = list(
            map(
                lambda fp: os.path.basename(fp),
                [file_path for file_path in file_paths if file_path.suffix.lower() == ".json"],
            )
        )
        file_names = list(map(lambda fp: os.path.basename(fp), file_paths))
        file_name_set = set(filter(lambda fn: not fn.endswith(".meta.json"), file_names))

        not_mapped_meta_files = [
            meta_file_name
            for meta_file_name in meta_file_names
            if not (meta_file_name.split(".meta.json")[0]) in file_name_set
        ]

        if len(not_mapped_meta_files) > 0:
            raise ValueError(
                f"Meta files without corresponding text files found: {not_mapped_meta_files}. "
                "Please make sure that for each meta file there is a corresponding text file."
                "The mapping needs to be done via file name '<file_name>' and '<file_name>.meta.json'. "
                "For example: 'file1.txt' and 'file1.txt.meta.json'."
            )

    @staticmethod
    def _preprocess_paths(paths: List[Path], spinner: yaspin.Spinner = None, recursive: bool = False) -> List[Path]:
        all_files = FilesService._get_file_paths(paths, recursive=recursive)
        file_paths = [
            path
            for path in all_files
            if path.is_file() and ((path.suffix in [".txt", ".pdf"]) or path.name.endswith("meta.json"))
        ]

        if len(file_paths) < len(all_files):
            logger.warning(
                "Skipping files with unsupported file format.",
                paths=paths,
                skipped_files=len(all_files) - len(file_paths),
            )

        if spinner is not None:
            spinner.text = "Validating files and metadata"
        FilesService._validate_file_paths(file_paths)

        return file_paths

    async def upload(
        self,
        workspace_name: str,
        paths: List[Path],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: int = 300,
        show_progress: bool = True,
        recursive: bool = False,
    ) -> None:
        """Upload a list of file or folder paths to a workspace.

        Upload files to a selected workspace using upload sessions. If blocking is True, the function waits until
        all files are uploaded and listed by deepset Cloud. If blocking is False, the function returns immediately after
        the upload of the files is done. Note: It can take a while until the files are listed in deepset Cloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :paths: Path to the folder to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :show_progress If True, shows a progress bar for S3 uploads
        :recursive: If True, recursively upload all files in the folder.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        logger.info("Getting valid files from file path. This may take a few minutes.", recursive=recursive)
        file_paths = []

        if show_progress:
            with yaspin().arc as sp:
                sp.text = "Finding uploadable files in the given paths"
                file_paths = self._preprocess_paths(paths, spinner=sp, recursive=recursive)
        else:
            file_paths = self._preprocess_paths(paths, recursive=recursive)

        await self.upload_file_paths(
            workspace_name=workspace_name,
            file_paths=file_paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
            show_progress=show_progress,
        )

    async def upload_texts(
        self,
        workspace_name: str,
        files: List[DeepsetCloudFile],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: int = 300,
        show_progress: bool = True,
    ) -> None:
        """
        Upload a list of raw texts to a workspace.

        Upload a list of raw texts to a selected workspace using upload sessions. This method accepts a list of DeepsetCloudFiles
        which contain raw text, file name, and optional meta data.

        If blocking is True, the function waits until all files are uploaded and listed by deepset Cloud.
        If blocking is False, the function returns immediately after the upload of the files is done.
        Note: It can take a while until the files are listed in deepset Cloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :files: List of DeepsetCloudFiles to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :show_progress If True, shows a progress bar for S3 uploads
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        # create session to upload files to
        async with self._create_upload_session(workspace_name=workspace_name, write_mode=write_mode) as upload_session:
            upload_summary = await self._s3.upload_texts(
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

    async def list_all(
        self,
        workspace_name: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        odata_filter: Optional[str] = None,
        batch_size: int = 100,
        timeout_s: int = 20,
    ) -> AsyncGenerator[List[File], None]:
        """List all files in a workspace.

        Returns an async generator that yields lists of files. The generator is finished when all files are listed.
        You can specfy the batch size per number of returned files with batch_size.

        :param workspace_name: Name of the workspace to use.
        :param name: odata_filter by file name.
        :param content: odata_filter by file content.
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
            if time.time() - start > timeout_s:
                raise TimeoutError(f"Listing all files in workspace {workspace_name} timed out.")
            response = await self._files.list_paginated(
                workspace_name,
                name=name,
                content=content,
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
