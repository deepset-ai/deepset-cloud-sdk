from typing import List
from unittest.mock import Mock

import httpx
import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.upload_sessions import (
    UploadSession,
    UploadSessionDetailList,
    UploadSessionIngestionStatus,
    UploadSessionsAPI,
)


@pytest.mark.asyncio
class TestCreateUploadSessions:
    async def test_create_and_close_upload_session(self, integration_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            result: UploadSession = await upload_session_client.create(workspace_name="sdk")

            assert result.session_id is not None
            assert result.documentation_url is not None
            assert result.expires_at is not None

            assert (
                result.aws_prefixed_request_config.url
                == "https://dc-dev-euc1-034167606153-user-files-upload.s3.amazonaws.com/"
            )
            assert result.aws_prefixed_request_config.fields["key"] is not None

            await upload_session_client.close(workspace_name="sdk", session_id=result.session_id)

            session_status = await upload_session_client.status(workspace_name="sdk", session_id=result.session_id)
            assert session_status.session_id is not None
            assert session_status.documentation_url is not None
            assert session_status.expires_at is not None
            assert session_status.ingestion_status == UploadSessionIngestionStatus(failed_files=0, finished_files=0)

    async def test_list_upload_session(self, integration_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            result: UploadSessionDetailList = await upload_session_client.list(
                workspace_name="sdk", limit=3, page_number=3
            )

            assert result.total > 0
            assert result.has_more == True
            assert result.data is not None
            assert len(result.data) == 3
