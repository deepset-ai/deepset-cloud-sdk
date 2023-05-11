from typing import List
from unittest.mock import Mock

import httpx
import pytest
import http
from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.upload_sessions import UploadSession, UploadSessionsAPI
from deepset_cloud_sdk.s3 import S3


@pytest.mark.asyncio
class TestCreateUploadSessions:
    async def test_create_session(self, integration_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            upload_session_client = UploadSessionsAPI(deepset_cloud_api)

            session: UploadSession = await upload_session_client.create(workspace_name="sdk")
            s3_client = S3()
            result = await s3_client.upload_file(
                file_name="test_sdk_file.txt",
                aws_prefixed_request_config=session.aws_prefixed_request_config,
                content="this is the file content",
            )
            assert result.status == http.HTTPStatus.CREATED
