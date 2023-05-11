"""Upload sessions API for deepset Cloud."""

import datetime
from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID

import structlog
from httpx import codes

from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI

logger = structlog.get_logger(__name__)


@dataclass
class AWSPrefixedRequesetConfig:
    """AWS prefixed request config.

    This prefixed request config can be used to send authenticated requests to AWS S3.
    """

    fields: Dict[str, Any]
    url: str


@dataclass
class UploadSession:
    """Upload session object."""

    session_id: UUID
    documentation_url: str
    expires_at: datetime.datetime
    aws_prefixed_request_config: AWSPrefixedRequesetConfig


class FailedToCreateUploadSession(Exception):
    """Raised if the upload session could not be created."""


class FailedToCloseUploadSession(Exception):
    """Raised if the upload session could not be closed."""


class UploadSessionsAPI:
    """Upload sessions API for deepset Cloud."""

    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        """
        Create FileAPI object.

        :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
        """
        self._deepset_cloud_api = deepset_cloud_api

    async def create(self, workspace_name: str) -> UploadSession:
        """Create upload session.

        This method creates an upload session for a given workspace. The upload session
        is valid for 24 hours. After that, a new upload session needs to be created.

        Each session needs to be closed to start the ingestion.

        :param workspace_name: Name of the workspace.
        :raises AssertionError: If the session could not be created.
        :return: UploadSession object.
        """
        response = await self._deepset_cloud_api.post(
            workspace_name=workspace_name, endpoint="upload_sessions", data={}
        )
        if response.status_code != codes.CREATED:
            logger.error(
                "Failed to create upload session.",
                status_code=response.status_code,
                response_body=response.text,
            )
            raise FailedToCreateUploadSession(f"Failed to create upload session. Status code: {response.status_code}.")
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

        This method closes an upload session for a given workspace. Once the session is closed, no more files can be
        uploaded to this session and the ingestion is automatically started.
        This means that your files will appear in the workspace after a short while.

        :param workspace_name: Name of the workspace.
        :param session_id: ID of the session.
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
            raise FailedToCloseUploadSession(f"Failed to close upload session. Status code: {response.status_code}.")
