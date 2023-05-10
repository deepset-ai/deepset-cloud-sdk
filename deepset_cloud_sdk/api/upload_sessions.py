"""
Upload sessions API for deepset Cloud.
"""

import datetime
import inspect
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from uuid import UUID

import structlog
from httpx import codes

from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI

logger = structlog.get_logger(__name__)


@dataclass
class AWSPrefixedRequesetConfig:
    fields: Dict[str, Any]
    url: str


@dataclass
class UploadSession:
    session_id: UUID
    documentation_url: str
    expires_at: datetime.datetime
    aws_prefixed_request_config: AWSPrefixedRequesetConfig


class UploadSessionsAPI:
    """Upload sessions API for deepset Cloud."""

    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        """
        Create FileAPI object.

        :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
        """
        self._deepset_cloud_api = deepset_cloud_api

    async def create(self, workspace_name: str) -> UploadSession:
        response = await self._deepset_cloud_api.post(
            workspace_name=workspace_name, endpoint="upload_sessions", data={}
        )
        assert response.status_code == codes.CREATED, "session could not be created"
        response_body = response.json()
        return UploadSession(
            session_id=response_body["session_id"],
            documentation_url=response_body["documentation_url"],
            expires_at=datetime.datetime.fromisoformat(response_body["expires_at"]),
            aws_prefixed_request_config=AWSPrefixedRequesetConfig(
                fields=response_body["aws_prefixed_request_config"]["fields"],
                url=response_body["aws_prefixed_request_config"]["url"],
            ),
        )
