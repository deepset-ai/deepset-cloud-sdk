"""Module for all file related operations."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, List
from unittest.mock import AsyncMock, Mock

import httpx
import structlog

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import UploadSessionsAPI, UploadSessionStatus

logger = structlog.get_logger(__name__)


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

    async def upload_file_paths(
        self, workspace_name: str, file_paths: List[Path], blocking: bool = True, timeout_s: int = 300
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
        upload_session = await self._upload_sessions.create(workspace_name=workspace_name)

        # upload file paths to session
        await self._aws.upload_files(upload_session=upload_session, file_paths=file_paths)

        # finalize session
        await self._upload_sessions.close(workspace_name=workspace_name, session_id=upload_session.session_id)

        # wait for ingestion to finish
        if blocking:
            start = time.time()
            ingested_files = 0
            while ingested_files < len(file_paths):
                if time.time() - start > timeout_s:
                    raise TimeoutError("Ingestion timed out.")

                upload_session_status: UploadSessionStatus = await self._upload_sessions.status(
                    workspace_name=workspace_name, session_id=upload_session.session_id
                )
                ingested_files = (
                    upload_session_status.ingestion_status.finished_files
                    + upload_session_status.ingestion_status.failed_files
                )
                logger.info(
                    "Waiting for ingestion to finish.",
                    finished_files=upload_session_status.ingestion_status.finished_files,
                    failed_files=upload_session_status.ingestion_status.failed_files,
                    total_files=len(file_paths),
                )
                time.sleep(1)
