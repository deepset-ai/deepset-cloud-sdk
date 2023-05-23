"""Upload sessions API for deepset Cloud."""

import datetime
import enum
from dataclasses import dataclass
from typing import Dict, List
from uuid import UUID

import structlog
from httpx import codes

from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.models import UserInfo

logger = structlog.get_logger(__name__)


@dataclass
class AWSPrefixedRequesetConfig:
    """AWS prefixed request config.

    This prefixed request config can be used to send authenticated requests to AWS S3.
    """

    fields: Dict[str, str]
    url: str


@dataclass
class UploadSession:
    """Upload session object."""

    session_id: UUID
    documentation_url: str
    expires_at: datetime.datetime
    aws_prefixed_request_config: AWSPrefixedRequesetConfig


class UploadSessionWriteModeEnum(str, enum.Enum):
    """Write mode for upload session."""

    KEEP = "KEEP"  # to keep duplicate files
    OVERWRITE = "OVERWRITE"  # to overwrite files
    FAIL = "FAIL"  # to fail if duplicate files are found


class UploadSessionStatusEnum(str, enum.Enum):
    """Status for upload session."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class UploadSessionDetail:
    """Detailed data class for upload session."""

    session_id: UUID
    created_by: UserInfo
    created_at: datetime.datetime
    expires_at: datetime.datetime
    write_mode: UploadSessionWriteModeEnum
    status: UploadSessionStatusEnum


@dataclass
class UploadSessionDetailList:
    """List of upload session details."""

    total: int
    data: List[UploadSessionDetail]
    has_more: bool


@dataclass
class UploadSessionIngestionStatus:
    """Upload session ingestion status.

    This status only contains the number of processed and therefore failed and finished files.
    The total number of uploaded files needs to be tracked by the client.
    """

    failed_files: int
    finished_files: int


@dataclass
class UploadSessionStatus:
    """Upload session status."""

    session_id: UUID
    expires_at: datetime.datetime
    documentation_url: str
    ingestion_status: UploadSessionIngestionStatus


class WriteMode(str, enum.Enum):
    """Enum for write modes."""

    OVERWRITE = "OVERWRITE"
    KEEP = "KEEP"
    FAIL = "FAIL"


class FailedToSendUploadSessionRequest(Exception):
    """Raised if the upload session could not be created."""


class UploadSessionsAPI:
    """Upload sessions API for deepset Cloud."""

    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        """
        Create FileAPI object.

        :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
        """
        self._deepset_cloud_api = deepset_cloud_api

    async def create(self, workspace_name: str, write_mode: WriteMode = WriteMode.KEEP) -> UploadSession:
        """Create upload session.

        This method creates an upload session for a given workspace. The upload session
        is valid for 24 hours. After that, you need to create a new upload session.

        You must close a session to start the ingestion.

        :param workspace_name: Name of the workspace.
        :raises FailedToSendUploadSessionRequest: If the session could not be created.
        :return: UploadSession object.
        """
        response = await self._deepset_cloud_api.post(
            workspace_name=workspace_name, endpoint="upload_sessions", data={"write_mode": write_mode.value}
        )
        if response.status_code != codes.CREATED:
            logger.error(
                "Failed to create upload session.",
                status_code=response.status_code,
                response_body=response.text,
            )
            raise FailedToSendUploadSessionRequest(
                f"Failed to create upload session. Status code: {response.status_code}."
            )
        response_body = response.json()
        return UploadSession(
            session_id=UUID(response_body["session_id"]),
            documentation_url=response_body["documentation_url"],
            expires_at=datetime.datetime.fromisoformat(response_body["expires_at"]),
            aws_prefixed_request_config=AWSPrefixedRequesetConfig(
                fields=response_body["aws_prefixed_request_config"]["fields"],
                url=response_body["aws_prefixed_request_config"]["url"],
            ),
        )

    async def close(self, workspace_name: str, session_id: UUID) -> None:
        """Close upload session.

        This method closes an upload session for a given workspace. Once the session is closed, you can't upload
        more files to this session and the ingestion is automatically started.
        This means that your files will appear in the workspace after a short while.

        :param workspace_name: Name of the workspace.
        :param session_id: ID of the session.
        :raises FailedToSendUploadSessionRequest: If the session could not be closed.
        :raises FailedToSendUploadSessionRequest: If the status could not be fetched.
        """
        response = await self._deepset_cloud_api.put(
            workspace_name=workspace_name, endpoint=f"upload_sessions/{session_id}", data={"status": "CLOSED"}
        )
        if response.status_code != codes.NO_CONTENT:
            logger.error(
                "Failed to close upload session.",
                status_code=response.status_code,
                response_body=response.text,
            )
            raise FailedToSendUploadSessionRequest(
                f"Failed to close upload session. Status code: {response.status_code}."
            )

    async def status(self, workspace_name: str, session_id: UUID) -> UploadSessionStatus:
        """Fetch upload session status.

        This method fetches the status of an upload session for a given workspace.

        :param workspace_name: Name of the workspace.
        :param session_id: ID of the session.
        :raises FailedToSendUploadSessionRequest: If the status could not be fetched.
        :return: UploadSessionStatus object.
        """
        response = await self._deepset_cloud_api.get(
            workspace_name=workspace_name, endpoint=f"upload_sessions/{session_id}"
        )
        if response.status_code != codes.OK:
            logger.error(
                "Failed to get upload session status.",
                status_code=response.status_code,
                response_body=response.text,
            )
            raise FailedToSendUploadSessionRequest(
                f"Failed to get upload session status. Status code: {response.status_code}."
            )
        response_body = response.json()
        return UploadSessionStatus(
            session_id=UUID(response_body["session_id"]),
            documentation_url=response_body["documentation_url"],
            expires_at=datetime.datetime.fromisoformat(response_body["expires_at"]),
            ingestion_status=UploadSessionIngestionStatus(
                failed_files=response_body["ingestion_status"]["failed_files"],
                finished_files=response_body["ingestion_status"]["finished_files"],
            ),
        )

    async def list(self, workspace_name: str, limit: int = 10, page_number: int = 1) -> UploadSessionDetailList:
        """List upload sessions.

        This method lists all upload sessions for a given workspace.

        :param workspace_name: Name of the workspace.
        :param limit: Number of upload sessions to return.
        :param page_number: Page number of the upload sessions.
        :raises FailedToSendUploadSessionRequest: If the list could not be fetched.
        :return: UploadSessionDetailList object.
        """
        response = await self._deepset_cloud_api.get(
            workspace_name=workspace_name,
            endpoint=f"upload_sessions",
            params={"limit": limit, "page_number": page_number},
        )
        if response.status_code != codes.OK:
            logger.error(
                "Failed to get upload session status.",
                status_code=response.status_code,
                response_body=response.text,
            )
            raise FailedToSendUploadSessionRequest(
                f"Failed to get upload session status. Status code: {response.status_code}."
            )
        response_body = response.json()
        return UploadSessionDetailList(
            total=response_body["total"],
            has_more=response_body["has_more"],
            data=[
                UploadSessionDetail(
                    session_id=UUID(upload_session["session_id"]),
                    created_by=UserInfo(
                        user_id=UUID(upload_session["created_by"]["user_id"]),
                        given_name=upload_session["created_by"]["given_name"],
                        family_name=upload_session["created_by"]["family_name"],
                    ),
                    expires_at=datetime.datetime.fromisoformat(upload_session["expires_at"]),
                    created_at=datetime.datetime.fromisoformat(upload_session["created_at"]),
                    write_mode=UploadSessionWriteModeEnum(upload_session["write_mode"]),
                    status=UploadSessionStatusEnum(upload_session["status"]),
                )
                for upload_session in response_body["data"]
            ],
        )
