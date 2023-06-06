import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from httpx import Response, codes

from deepset_cloud_sdk._api.upload_sessions import (
    FailedToSendUploadSessionRequest,
    UploadSession,
    UploadSessionDetailList,
    UploadSessionsAPI,
    UploadSessionStatusEnum,
    UploadSessionWriteModeEnum,
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

        result: UploadSession = await upload_session_client.create(workspace_name="sdk_read")

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
        with pytest.raises(FailedToSendUploadSessionRequest):
            await upload_session_client.create(workspace_name="sdk_read")


@pytest.mark.asyncio
class TestCloseUploadSessions:
    async def test_close_session(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()

        mocked_deepset_cloud_api.put.return_value = Response(status_code=codes.NO_CONTENT)

        await upload_session_client.close(workspace_name="sdk_read", session_id=session_id)
        mocked_deepset_cloud_api.put.assert_called_once_with(
            workspace_name="sdk_read", endpoint=f"upload_sessions/{session_id}", data={"status": "CLOSED"}
        )

    async def test_close_session_failed(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()

        mocked_deepset_cloud_api.put.return_value = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        with pytest.raises(FailedToSendUploadSessionRequest):
            await upload_session_client.close(workspace_name="sdk_read", session_id=session_id)


@pytest.mark.asyncio
class TestStatusUploadSessions:
    async def test_get_session_status(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()
        expires_at = datetime.datetime.now()

        mocked_deepset_cloud_api.get.return_value = Response(
            status_code=codes.OK,
            json={
                "session_id": str(session_id),
                "expires_at": expires_at.isoformat(),
                "documentation_url": "https://docs.cloud.deepset.ai/docs",
                "ingestion_status": {"failed_files": 0, "finished_files": 0},
            },
        )

        upload_session_status = await upload_session_client.status(workspace_name="sdk_read", session_id=session_id)
        assert upload_session_status.session_id == session_id
        assert upload_session_status.expires_at == expires_at
        assert upload_session_status.documentation_url == "https://docs.cloud.deepset.ai/docs"
        assert upload_session_status.ingestion_status.failed_files == 0
        assert upload_session_status.ingestion_status.finished_files == 0

        mocked_deepset_cloud_api.get.assert_called_once_with(
            workspace_name="sdk_read", endpoint=f"upload_sessions/{session_id}"
        )

    async def test_get_session_status_with_retry(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()
        expires_at = datetime.datetime.now()

        mocked_deepset_cloud_api.get.side_effect = [
            Response(status_code=codes.BAD_GATEWAY),
            Response(
                status_code=codes.OK,
                json={
                    "session_id": str(session_id),
                    "expires_at": expires_at.isoformat(),
                    "documentation_url": "https://docs.cloud.deepset.ai/docs",
                    "ingestion_status": {"failed_files": 0, "finished_files": 0},
                },
            ),
        ]

        upload_session_status = await upload_session_client.status(workspace_name="sdk_read", session_id=session_id)
        assert upload_session_status.session_id == session_id
        assert upload_session_status.expires_at == expires_at
        assert upload_session_status.documentation_url == "https://docs.cloud.deepset.ai/docs"
        assert upload_session_status.ingestion_status.failed_files == 0
        assert upload_session_status.ingestion_status.finished_files == 0

    async def test_get_session_status_failed(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()

        mocked_deepset_cloud_api.get.return_value = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        with pytest.raises(FailedToSendUploadSessionRequest):
            await upload_session_client.status(workspace_name="sdk_read", session_id=session_id)


@pytest.mark.asyncio
class TestListUploadSessions:
    async def test_list_sessions(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()
        timestamp = datetime.datetime.now()
        user_id = uuid4()

        mocked_deepset_cloud_api.get.return_value = Response(
            status_code=codes.OK,
            json={
                "data": [
                    {
                        "session_id": str(session_id),
                        "created_by": {
                            "given_name": "Kristof",
                            "family_name": "Test",
                            "user_id": str(user_id),
                        },
                        "created_at": timestamp.isoformat(),
                        "expires_at": timestamp.isoformat(),
                        "write_mode": "KEEP",
                        "status": "OPEN",
                    },
                ],
                "has_more": True,
                "total": 23,
            },
        )
        result: UploadSessionDetailList = await upload_session_client.list(
            workspace_name="sdk_read", limit=1, page_number=10
        )
        assert result.has_more is True
        assert result.total == 23
        assert len(result.data) == 1
        assert result.data[0].session_id == session_id
        assert result.data[0].created_by.given_name == "Kristof"
        assert result.data[0].created_by.family_name == "Test"
        assert result.data[0].created_by.user_id == user_id
        assert result.data[0].created_at == timestamp
        assert result.data[0].expires_at == timestamp
        assert result.data[0].write_mode == UploadSessionWriteModeEnum.KEEP
        assert result.data[0].status == UploadSessionStatusEnum.OPEN

    async def test_list_sessions_with_retry(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        session_id = uuid4()
        timestamp = datetime.datetime.now()
        user_id = uuid4()

        mocked_deepset_cloud_api.get.side_effect = [
            Response(status_code=codes.BAD_GATEWAY),
            Response(
                status_code=codes.OK,
                json={
                    "data": [
                        {
                            "session_id": str(session_id),
                            "created_by": {
                                "given_name": "Kristof",
                                "family_name": "Test",
                                "user_id": str(user_id),
                            },
                            "created_at": timestamp.isoformat(),
                            "expires_at": timestamp.isoformat(),
                            "write_mode": "KEEP",
                            "status": "OPEN",
                        },
                    ],
                    "has_more": True,
                    "total": 23,
                },
            ),
        ]
        result: UploadSessionDetailList = await upload_session_client.list(
            workspace_name="sdk_read", limit=1, page_number=10
        )
        assert result.has_more is True
        assert result.total == 23
        assert len(result.data) == 1
        assert result.data[0].session_id == session_id
        assert result.data[0].created_by.given_name == "Kristof"
        assert result.data[0].created_by.family_name == "Test"
        assert result.data[0].created_by.user_id == user_id
        assert result.data[0].created_at == timestamp
        assert result.data[0].expires_at == timestamp
        assert result.data[0].write_mode == UploadSessionWriteModeEnum.KEEP
        assert result.data[0].status == UploadSessionStatusEnum.OPEN

    async def test_list_sessions_failed(
        self, upload_session_client: UploadSessionsAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        mocked_deepset_cloud_api.get.return_value = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        with pytest.raises(FailedToSendUploadSessionRequest):
            await upload_session_client.list(workspace_name="sdk_read")
