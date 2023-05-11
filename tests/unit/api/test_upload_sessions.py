import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from httpx import Response, codes

from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.api.upload_sessions import (
    FailedToCloseUploadSession,
    FailedToCreateUploadSession,
    UploadSession,
    UploadSessionsAPI,
)


@pytest.fixture
def upload_session_client(mocked_deepset_cloud_api: Mock) -> UploadSessionsAPI:
    return UploadSessionsAPI(mocked_deepset_cloud_api)


@pytest.mark.asyncio
class TestCreateUploadSessions:
    async def test_create_session(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()
        expires_at = datetime.datetime.now()
        mocked_deepset_cloud_api.post.return_value = Response(
            status_code=codes.CREATED,
            json={
                "session_id": str(session_id),
                "documentation_url": "documentation_url",
                "expires_at": expires_at.isoformat(),
                "aws_prefixed_request_config": {
                    "url": "https://dc-dev-euc1-034167606153-user-files-upload.s3.amazonaws.com/",
                    "fields": {"key": "key"},
                },
            },
        )

        result: UploadSession = await upload_session_client.create(workspace_name="sdk")

        assert result.session_id == session_id

        assert result.documentation_url == "documentation_url"
        assert result.expires_at == expires_at
        assert (
            result.aws_prefixed_request_config.url
            == "https://dc-dev-euc1-034167606153-user-files-upload.s3.amazonaws.com/"
        )
        assert result.aws_prefixed_request_config.fields["key"] == "key"

    async def test_create_session_fails(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        mocked_deepset_cloud_api.post.return_value = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        with pytest.raises(FailedToCreateUploadSession):
            await upload_session_client.create(workspace_name="sdk")


@pytest.mark.asyncio
class TestCloseUploadSessions:
    async def test_close_session(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()

        mocked_deepset_cloud_api.put.return_value = Response(status_code=codes.NO_CONTENT)

        await upload_session_client.close(workspace_name="sdk", session_id=session_id)
        mocked_deepset_cloud_api.put.assert_called_once_with(
            workspace_name="sdk", endpoint=f"upload_sessions/{session_id}", data={"status": "CLOSED"}
        )

    async def test_close_session_failed(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()

        mocked_deepset_cloud_api.put.return_value = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        with pytest.raises(FailedToCloseUploadSession):
            await upload_session_client.close(workspace_name="sdk", session_id=session_id)
