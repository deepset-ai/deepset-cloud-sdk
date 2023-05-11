from pathlib import Path
from unittest.mock import Mock

import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.upload_sessions import (
    UploadSession,
    UploadSessionIngestionStatus,
    UploadSessionStatus,
)
from deepset_cloud_sdk.service.files_service import FilesService


@pytest.fixture
def file_service(mocked_upload_sessions_api: Mock, mocked_files_api: Mock, mocked_aws: Mock) -> FilesService:
    return FilesService(upload_sessions=mocked_upload_sessions_api, files=mocked_files_api, aws=mocked_aws)


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(
        self,
        file_service: FilesService,
        mocked_upload_sessions_api: Mock,
        upload_session_response: UploadSession,
        mocked_aws: Mock,
    ) -> None:
        mocked_upload_sessions_api.create.return_value = upload_session_response
        mocked_upload_sessions_api.status.return_value = UploadSessionStatus(
            session_id=upload_session_response.session_id,
            expires_at=upload_session_response.expires_at,
            documentation_url=upload_session_response.documentation_url,
            ingestion_status=UploadSessionIngestionStatus(
                failed_files=0,
                finished_files=1,
            ),
        )
        await file_service.upload_file_paths(
            workspace_name="test_workspace", file_paths=[Path("./tmp/my-file")], blocking=True, timeout_s=300
        )

        mocked_upload_sessions_api.create.assert_called_once_with(workspace_name="test_workspace")

        mocked_aws.upload_files.assert_called_once_with(
            upload_session=upload_session_response, file_paths=[Path("./tmp/my-file")]
        )

        mocked_upload_sessions_api.close.assert_called_once_with(
            workspace_name="test_workspace", session_id=upload_session_response.session_id
        )
        mocked_upload_sessions_api.status.assert_called_once_with(
            workspace_name="test_workspace", session_id=upload_session_response.session_id
        )

    async def test_upload_file_paths_with_timeout(
        self,
        file_service: FilesService,
        mocked_upload_sessions_api: Mock,
        upload_session_response: UploadSession,
    ) -> None:
        mocked_upload_sessions_api.create.return_value = upload_session_response
        mocked_upload_sessions_api.status.return_value = UploadSessionStatus(
            session_id=upload_session_response.session_id,
            expires_at=upload_session_response.expires_at,
            documentation_url=upload_session_response.documentation_url,
            ingestion_status=UploadSessionIngestionStatus(
                failed_files=0,
                finished_files=0,
            ),
        )
        with pytest.raises(TimeoutError):
            await file_service.upload_file_paths(
                workspace_name="test_workspace", file_paths=[Path("./tmp/my-file")], blocking=True, timeout_s=0
            )


@pytest.mark.asyncio
class TestUtilsFileService:
    async def test_factory(self, unit_config: CommonConfig) -> None:
        async with FilesService.factory(unit_config) as file_service:
            assert isinstance(file_service, FilesService)
