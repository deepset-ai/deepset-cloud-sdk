"""
File API for deepset Cloud.

This module takes care of all file-related API calls to deepset Cloud, including uploading, downloading, listing, and
deleting files.
"""

import datetime
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import structlog
from httpx import codes

from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI

logger = structlog.get_logger(__name__)


class FileNotFoundInDeepsetCloudException(Exception):
    """Exception raised when a file is not found."""


@dataclass
class File:
    """File primitive from deepset Cloud. This dataclass is used for all file-related operations that don't include thea actual file content."""

    file_id: UUID
    url: str
    name: str
    size: int
    created_at: datetime.datetime
    meta: Dict[str, Any]

    @classmethod
    def from_dict(cls, env: Dict[str, Any]) -> Any:
        """Parse a dictionary into a File object.

        Ignores keys that don't exist.

        :param env: Dictionary to parse.
        """
        to_parse = {k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        to_parse["created_at"] = datetime.datetime.fromisoformat(to_parse["created_at"])
        to_parse["file_id"] = UUID(to_parse["file_id"])
        return cls(**to_parse)


@dataclass
class FileList:
    """List of files from deepset Cloud. This dataclass is used for all file-related operations that return a list of files."""

    total: int
    data: List[File]
    has_more: bool


class FilesAPI:
    """File API for deepset Cloud.

    This module takes care of all file-related API calls to deepset Cloud, including
    uploading, downloading, listing, and deleting files.

    :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
    """

    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        """
        Create FileAPI object.

        :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
        """
        self._deepset_cloud_api = deepset_cloud_api

    async def list_paginated(
        self,
        workspace_name: str,
        limit: int = 100,
        name: Optional[str] = None,
        content: Optional[str] = None,
        odata_filter: Optional[str] = None,
        after_value: Optional[Any] = None,
        after_file_id: Optional[UUID] = None,
    ) -> FileList:
        """
        List files in a workspace using cursor-based pagination.

        :param workspace_name: Name of the workspace to use.
        :param limit: Number of files to return per page.
        :param name: Name of the file to odata_filter by.
        :param content: Content of the file to odata_filter by.
        :param odata_filter: Odata odata_filter to apply.
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

        # odata odata_filter for file meta
        if odata_filter:
            params["filter"] = odata_filter

        response = await self._deepset_cloud_api.get(workspace_name, "files", params=params)
        assert response.status_code == codes.OK, f"Failed to list files: {response.text}"
        response_body = response.json()
        total = response_body["total"]
        data = response_body["data"]
        has_more = response_body["has_more"]
        return FileList(total=total, data=[File.from_dict(d) for d in data], has_more=has_more)

    @staticmethod
    def _available_file_name(file_path: Path, suffix: str = "_1") -> str:
        logger.warning("File already exists. Renaming file to avoid overwriting.", file_path=str(file_path))
        base = file_path.stem
        ext = file_path.suffix
        new_filename = file_path.with_name(f"{base}{suffix}{ext}")
        while new_filename.exists():
            suffix = f"_{int(suffix[1:]) + 1}"
            new_filename = file_path.with_name(f"{base}{suffix}{ext}")
        return str(new_filename)

    async def _save_to_disk(self, file_dir: Path, file_name: str, content: bytes) -> str:
        """Save the given content to disk.

        If there is a collision, the file name is changed to avoid overwriting.
        This new name is returned by the function.

        :param file_dir: Path to the file.
        :param file_name: Name of the file.
        :param content: Content of the file.
        :return: The new file name.
        """
        # Check if the directory exists, and create it if necessary
        file_dir.mkdir(parents=True, exist_ok=True)

        new_filename: str = file_name
        file_path = file_dir / file_name
        if file_path.exists():
            new_filename = self._available_file_name(file_path)

        with (file_dir / new_filename).open("wb") as file:
            file.write(content)
        return new_filename

    async def download(
        self,
        workspace_name: str,
        file_id: UUID,
        file_name: str,
        include_meta: bool = True,
        file_dir: Optional[Union[Path, str]] = None,
    ) -> None:
        """Download a single file from a workspace.

        :param workspace_name: Name of the workspace to use.
        :param file_id: ID of the file to download.
        :param include_meta: Whether to include the file meta in the folder.
        """
        if file_dir is None:
            file_dir = Path.cwd()

        if isinstance(file_dir, str):
            # format dir to Path and take relative path into account
            file_dir = Path(file_dir).resolve()

        response = await self._deepset_cloud_api.get(workspace_name, f"files/{file_id}")
        if response.status_code == codes.NOT_FOUND:
            raise FileNotFoundInDeepsetCloudException(f"Failed to download raw file: {response.text}")
        if response.status_code != codes.OK:
            raise Exception(f"Failed to download raw file: {response.text}")
        new_local_file_name: str = await self._save_to_disk(
            file_dir=file_dir, file_name=file_name, content=response.content
        )

        if include_meta:
            response = await self._deepset_cloud_api.get(workspace_name, f"files/{file_id}/meta")
            if response.status_code == codes.NOT_FOUND:
                raise FileNotFoundInDeepsetCloudException(f"Failed to download raw file: {response.text}")
            if response.status_code != codes.OK:
                raise Exception(f"Failed to download raw file: {response.text}")
            await self._save_to_disk(
                file_dir=file_dir,
                file_name=f"{new_local_file_name}.meta.json",
                content=response.content,
            )
