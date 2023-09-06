import uuid

import pytest

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.upload_sessions import (
    FileIngestionStatus,
    UploadSession,
    UploadSessionDetailList,
    UploadSessionFileList,
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

    async def test_list_upload_session_files(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with DeepsetCloudAPI.factory(integration_config) as deepset_cloud_api:
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            sessions: UploadSessionDetailList = await upload_session_client.list(
                workspace_name=workspace_name, limit=3, page_number=3
            )

            sessions.data[0].session_id

            result: UploadSessionFileList = await upload_session_client.list_session_files(
                workspace_name="default",
                limit=1,
                page_number=1,
                session_id=uuid.UUID("f5866c26-e0a4-464f-87ed-9a186a984b0e"),
                ingestion_status=FileIngestionStatus.FINISHED,
            )

            assert result.total > 0
            assert result.has_more is True
            assert result.data is not None
            assert len(result.data) == 1
            assert result.data[0].ingestion_status == FileIngestionStatus.FINISHED.name
            assert result.data[0].file_ingestion_id is not None
            assert result.data[0].name is not None
