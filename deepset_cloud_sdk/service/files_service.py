"""Module for all file related operations."""
from __future__ import annotations

import enum
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import httpx
import structlog

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import (
    UploadSession,
    UploadSessionsAPI,
    UploadSessionStatus,
    WriteMode,
)

logger = structlog.get_logger(__name__)


@dataclass
class DeepsetCloudFile:
    """Dataclass for files in deepsetCloud."""

    text: str
    name: str
    meta: Optional[Dict[str, Any]] = None


class FilesService:
    """Service for all file related operations."""

    def __init__(self, upload_sessions: UploadSessionsAPI, files: FilesAPI, aws: Mock):
        """Initialize the service.

        :param upload_sessions: API for upload sessions.
        :param files: API for files.
        :param aws: AWS client.
        """
        self._upload_sessions = upload_sessions
        self._files = files
        self._aws = aws

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[FilesService, None]:
        """Create a new instance of the service.

        :param config: CommonConfig object.
        :param client: httpx client.
        :return: New instance of the service.
        """
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(config, client=client)
            files_api = FilesAPI(deepset_cloud_api)
            upload_sessions_api = UploadSessionsAPI(deepset_cloud_api)

            yield cls(upload_sessions_api, files_api, AsyncMock())

    async def _wait_for_finished(self, workspace_name: str, session_id: UUID, total_files: int, timeout_s: int) -> None:
        start = time.time()
        ingested_files = 0
        while ingested_files < total_files:
            if time.time() - start > timeout_s:
                raise TimeoutError("Ingestion timed out.")

            upload_session_status: UploadSessionStatus = await self._upload_sessions.status(
                workspace_name=workspace_name, session_id=session_id
            )
            ingested_files = (
                upload_session_status.ingestion_status.finished_files
                + upload_session_status.ingestion_status.failed_files
            )
            logger.info(
                "Waiting for ingestion to finish.",
                finished_files=upload_session_status.ingestion_status.finished_files,
                failed_files=upload_session_status.ingestion_status.failed_files,
                total_files=total_files,
            )
            time.sleep(1)

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
    ) -> None:
        """Upload a list of files to a workspace.

        Upload a list of files via upload sessions to a selected workspace. If blocking is True, the function waits until
        all files are uploaded and listed by deepsetCloud. If blocking is False, the function returns immediately after
        the upload of the files is done. Note: It can take a while until the files are listed in deepsetCloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :file_paths: List of file paths to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        # create session to upload files to
        async with self._create_upload_session(workspace_name=workspace_name, write_mode=write_mode) as upload_session:
            await self._aws.upload_files(upload_session=upload_session, file_paths=file_paths)

        # wait for ingestion to finish
        if blocking:
            await self._wait_for_finished(
                workspace_name=workspace_name,
                session_id=upload_session.session_id,
                total_files=len(file_paths),
                timeout_s=timeout_s,
            )

    async def upload_folder(
        self,
        workspace_name: str,
        folder_path: Path,
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: int = 300,
    ) -> None:
        """Upload a folder to a workspace.

        Upload a folder via upload sessions to a selected workspace. If blocking is True, the function waits until
        all files are uploaded and listed by deepsetCloud. If blocking is False, the function returns immediately after
        the upload of the files is done. Note: It can take a while until the files are listed in deepsetCloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :folder_path: Path to the folder to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        all_files = [path for path in folder_path.glob("**/*")]

        file_paths = [
            path
            for path in all_files
            if path.is_file() and ((path.suffix in [".txt", ".pdf"]) or path.name.endswith("meta.json"))
        ]
        if len(file_paths) < len(all_files):
            logger.warning(
                "Skipping files with unsupported file format.",
                folder_path=folder_path,
                skipped_files=len(all_files) - len(file_paths),
            )

        await self.upload_file_paths(
            workspace_name=workspace_name,
            file_paths=file_paths,
            write_mode=write_mode,
            blocking=blocking,
            timeout_s=timeout_s,
        )

    async def upload_texts(
        self,
        workspace_name: str,
        dc_files: List[DeepsetCloudFile],
        write_mode: WriteMode = WriteMode.KEEP,
        blocking: bool = True,
        timeout_s: int = 300,
    ) -> None:
        """
        Upload a list of raw texts to a workspace.

        Upload a list of raw texts via upload sessions to a selected workspace. This method accepts a list of DeepsetCloudFiles
        which contain the raw text, file name and optional meta data.

        If blocking is True, the function waits until all files are uploaded and listed by deepsetCloud.
        If blocking is False, the function returns immediately after the upload of the files is done.
        Note: It can take a while until the files are listed in deepsetCloud.

        :param workspace_name: Name of the workspace to upload the files to.
        :dc_files: List of DeepsetCloudFiles to upload.
        :blocking: If True, blocks until the ingestion is finished.
        :timeout_s: Timeout in seconds for the blocking ingestion.
        :raises TimeoutError: If blocking is True and the ingestion takes longer than timeout_s.
        """
        # create session to upload files to
        async with self._create_upload_session(workspace_name=workspace_name, write_mode=write_mode) as upload_session:
            await self._aws.upload_texts(upload_session=upload_session, dc_files=dc_files)

        if blocking:
            await self._wait_for_finished(
                workspace_name=workspace_name,
                session_id=upload_session.session_id,
                total_files=len(dc_files),
                timeout_s=timeout_s,
            )
