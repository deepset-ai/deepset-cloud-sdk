from unittest.mock import AsyncMock, Mock
from uuid import UUID

from deepset_cloud_sdk._api.pipelines import FileIndexingStatus
from deepset_cloud_sdk._service.pipeline_service import PipelinesService
import pytest

from deepset_cloud_sdk._api.config import CommonConfig


@pytest.fixture
def pipelines_service(mocked_pipelines: Mock) -> PipelinesService:
    return PipelinesService(pipelines=mocked_pipelines)


@pytest.mark.asyncio
class TestUtilsPipelinesService:
    async def test_factory(self, unit_config: CommonConfig) -> None:
        async with PipelinesService.factory(unit_config) as pipelines_service:
            assert isinstance(pipelines_service, PipelinesService)


@pytest.mark.asyncio
class TestGetFileIds:
    async def test_get_file_ids(
        self,
        mocked_pipelines: Mock,
        pipeline_service: PipelinesService,
    ) -> None:
        mocked_pipelines.get_pipeline_file_ids = AsyncMock(return_value=[UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")])
        returned_file_ids = await pipeline_service.get_pipeline_file_ids(
            workspace_name="test_workspace",
            pipeline_name="test_pipeline",
            status=FileIndexingStatus.INDEXED_NO_DOCUMENTS,
        )
        assert returned_file_ids == [UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")], "Unexpected file ids"

        mocked_pipelines.get_pipeline_file_ids.assert_called_once_with(
            pipeline_name="test_pipeline",
            workspace_name="test_workspace",
            status=FileIndexingStatus.INDEXED_NO_DOCUMENTS,
        )
