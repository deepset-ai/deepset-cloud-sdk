"""Module for all file related operations."""


from io import BufferedReader
import time
from pathlib import Path
from typing import Callable, List, Tuple
from unittest.mock import Mock

import structlog

from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import UploadSessionsAPI, UploadSessionStatus
from deepset_cloud_sdk.s3.upload import S3
import os

logger = structlog.get_logger(__name__)


class FilesService:
    """Service for all file related operations."""

    def __init__(self, upload_sessions: UploadSessionsAPI, files: FilesAPI, s3: S3):
        """Initialize the service.

        :param upload_sessions: API for upload sessions.
        :param files: API for files.
        :param aws: AWS client.
        """
        self._upload_sessions = upload_sessions
        self._files = files
        self._s3 = s3

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

        def get_file(file_path: str) -> Tuple[str, BufferedReader]:
            file = open(file_path, "rb")
            file_name = os.path.basename(file_path)
            return (file_name, file)

        get_files: List[Callable[[], Tuple[str, str]]] = []

        for path in file_paths:
            get_files.append(lambda: get_file(path))

        await self._s3.upload_files(upload_session=upload_session, get_files=get_files)

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
