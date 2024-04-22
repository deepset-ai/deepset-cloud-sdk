"""
Pipeline API for deepset Cloud.

This module takes care of all pipeline-related API calls to deepset Cloud.
"""

from enum import Enum
from typing import Dict, List
from uuid import UUID

import structlog
from httpx import codes

from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI

logger = structlog.get_logger(__name__)


class FileIndexingStatus(str, Enum):
    """File indexing status."""

    FAILED = "FAILED"
    INDEXED_NO_DOCUMENTS = "INDEXED_NO_DOCUMENTS"


class PipelineNotFoundException(Exception):
    """Raised if pipeline was not found."""


class FailedToFetchFileIdsException(Exception):
    """Failed fetching pipeline files."""


class PipelinesAPI:
    """Pipeline API for deepset Cloud.

    This module takes care of all pipeline-related API calls to deepset Cloud.

    :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
    """

    def __init__(self, deepset_cloud_api: DeepsetCloudAPI) -> None:
        """
        Create FileAPI object.

        :param deepset_cloud_api: Instance of the DeepsetCloudAPI.
        """
        self._deepset_cloud_api = deepset_cloud_api

    async def get_pipeline_file_ids(
        self, pipeline_name: str, workspace_name: str, status: FileIndexingStatus = FileIndexingStatus.FAILED
    ) -> List[UUID]:
        """Get file ids that failed or did not create documents during indexing.

        :param pipeline_name: Name of the pipeline that indexed files.
        :param workspace_name: Name of the workspace.
        :param status: Status that should be used for fetching files
        """
        params: Dict[str, str] = {"status": status}
        response = await self._deepset_cloud_api.get(workspace_name, f"pipelines/{pipeline_name}/files", params=params)
        if response.status_code == codes.NOT_FOUND:
            raise PipelineNotFoundException()
        if response.status_code != codes.OK:
            raise FailedToFetchFileIdsException(response.text)
        file_ids: List[UUID] = [UUID(_id) for _id in response.json()]
        return file_ids
