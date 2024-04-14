"""Module for all file-related operations."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List
from uuid import UUID

import structlog

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.pipelines import FileIndexingStatus, PipelinesAPI

logger = structlog.get_logger(__name__)


class PipelinesService:
    """Service for all pipeline-related operations."""

    def __init__(self, pipelines: PipelinesAPI):
        """Initialize the service.

        :param pipelines: API for pipelines.
        """
        self._pipelines = pipelines

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[PipelinesService, None]:
        """Create a new instance of the service.

        :param config: CommonConfig object.
        :return: New instance of the service.
        """
        async with DeepsetCloudAPI.factory(config) as deepset_cloud_api:
            yield cls(PipelinesAPI(deepset_cloud_api))

    async def get_pipeline_file_ids(
        self, pipeline_name: str, workspace_name: str, status: FileIndexingStatus = FileIndexingStatus.FAILED
    ) -> List[UUID]:
        return await self._pipelines.get_pipeline_file_ids(
            pipeline_name=pipeline_name, workspace_name=workspace_name, status=status
        )
