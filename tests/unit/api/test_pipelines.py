from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest

from deepset_cloud_sdk._api.pipelines import (
    FailedToFetchFileIdsException,
    FileIndexingStatus,
    PipelineNotFoundException,
    PipelinesAPI,
)


@pytest.fixture
def pipelines_api(mocked_deepset_cloud_api: Mock) -> PipelinesAPI:
    return PipelinesAPI(mocked_deepset_cloud_api)


@pytest.mark.asyncio
class TestGetPipelineFileIDs:
    async def test_get_pipeline_file_ids(self, pipelines_api: PipelinesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.get.return_value = httpx.Response(
            status_code=httpx.codes.OK,
            json=["cd16435f-f6eb-423f-bf6f-994dc8a36a10", "cd16435f-f6eb-423f-bf6f-994dc8a36a13"],
        )
        result = await pipelines_api.get_pipeline_file_ids(
            workspace_name="test_workspace",
            pipeline_name="test_pipeline",
            status=FileIndexingStatus.INDEXED_NO_DOCUMENTS,
        )
        assert result == [UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"), UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a13")]

    async def test_get_pipeline_file_ids_with_not_found_pipeline(
        self, pipelines_api: PipelinesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        mocked_deepset_cloud_api.get.return_value = httpx.Response(
            status_code=httpx.codes.NOT_FOUND,
            json=[],
        )
        with pytest.raises(PipelineNotFoundException):
            await pipelines_api.get_pipeline_file_ids(
                workspace_name="test_workspace",
                pipeline_name="test_pipeline",
                status=FileIndexingStatus.INDEXED_NO_DOCUMENTS,
            )

    async def test_get_pipeline_file_ids_with_api_error(
        self, pipelines_api: PipelinesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        mocked_deepset_cloud_api.get.return_value = httpx.Response(
            status_code=httpx.codes.SERVICE_UNAVAILABLE,
            json=[],
        )
        with pytest.raises(FailedToFetchFileIdsException):
            await pipelines_api.get_pipeline_file_ids(
                workspace_name="test_workspace",
                pipeline_name="test_pipeline",
                status=FileIndexingStatus.INDEXED_NO_DOCUMENTS,
            )
