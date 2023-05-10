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
class File:
    file_id: UUID
    url: str
    name: str
    size: int
    created_at: datetime.datetime
    meta: Dict[str, Any]

    @classmethod
    def from_dict(cls, env: Dict[str, Any]) -> Any:
        to_parse = {k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        to_parse["created_at"] = datetime.datetime.fromisoformat(to_parse["created_at"])
        to_parse["file_id"] = UUID(to_parse["file_id"])
        return cls(**to_parse)


@dataclass
class FileList:
    total: int
    data: List[File]
    has_more: bool


class FilesAPI:
    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        self._deepset_cloud_api = deepset_cloud_api

    async def list_paginated(
        self,
        workspace_name: str,
        limit: int = 100,
        name: Optional[str] = None,
        content: Optional[str] = None,
        filter: Optional[str] = None,
        after_value: Optional[Any] = None,
        after_file_id: Optional[UUID] = None,
    ) -> FileList:
        """
        List files in a workspace, paginated with cursor based pagination.

        :param workspace_name: Name of the workspace to use.
        :param limit: Number of files to return per page.
        :param name: Name of the file to filter by.
        :param content: Content of the file to filter by.
        :param filter: Odata Filter to apply.
        :param after_value: Value to start after.
        :param after_file_id: File ID to start after.
        """
        params: Dict[str, Union[str, int]] = {"limit": limit}
        if after_value and after_file_id:
            params["after_value"] = (
                after_value.isoformat() if isinstance(after_value, datetime.datetime) else str(after_value)
            )
            params["after_file_id"] = str(after_file_id)

        # substring match file name
        if name:
            params["name"] = name

        # content search file
        if content:
            params["content"] = content

        # odata filter for file meta
        if filter:
            params["filter"] = filter

        response = await self._deepset_cloud_api.get(workspace_name, "files", params=params)
        assert response.status_code == codes.OK, f"Failed to list files: {response.text}"
        response_body = response.json()
        total = response_body["total"]
        data = response_body["data"]
        has_more = response_body["has_more"]
        return FileList(total=total, data=[File.from_dict(d) for d in data], has_more=has_more)

    async def list_all(
        self, workspace_name: str, batch_size: int = 100, timeout: int = 20
    ) -> AsyncGenerator[List[File], None]:
        """
        List all files in a workspace.

        :param workspace_name: Name of the workspace to use.
        """
        start = time.time()
        has_more = True

        after_value = None
        after_file_id = None
        while time.time() - start < timeout and has_more:
            response = await self.list_paginated(
                workspace_name,
                limit=batch_size,
                after_file_id=after_file_id,
                after_value=after_value,
            )
            has_more = response.has_more
            after_value = response.data[-1].created_at
            after_file_id = response.data[-1].file_id
            yield response.data
