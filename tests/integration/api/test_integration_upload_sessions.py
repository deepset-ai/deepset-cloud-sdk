import pytest

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSession,
    UploadSessionDetailList,
    UploadSessionIngestionStatus,
    UploadSessionsAPI,
)


@pytest.fixture
def workspace_name() -> str:
    return "sdk_read"


@pytest.mark.asyncio
class TestCreateUploadSessions:
    async def test_create_and_close_upload_session(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with DeepsetCloudAPI.factory(integration_config) as deepset_cloud_api:
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            result: UploadSession = await upload_session_client.create(workspace_name=workspace_name)
            assert result.session_id is not None
            assert result.documentation_url is not None
            assert result.expires_at is not None

            assert "-user-files-upload.s3.amazonaws.com/" in result.aws_prefixed_request_config.url

            assert result.aws_prefixed_request_config.fields["key"] is not None

            await upload_session_client.close(workspace_name=workspace_name, session_id=result.session_id)

            session_status = await upload_session_client.status(
                workspace_name=workspace_name, session_id=result.session_id
            )
            assert session_status.session_id is not None
            assert session_status.documentation_url is not None
            assert session_status.expires_at is not None
            assert session_status.ingestion_status == UploadSessionIngestionStatus(failed_files=0, finished_files=0)

    async def test_list_upload_session(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with DeepsetCloudAPI.factory(integration_config) as deepset_cloud_api:
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            result: UploadSessionDetailList = await upload_session_client.list(
                workspace_name=workspace_name, limit=3, page_number=3
            )

            assert result.total > 0
            assert result.has_more is True
            assert result.data is not None
            assert len(result.data) == 3
