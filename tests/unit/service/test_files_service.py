import datetime
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from _pytest.monkeypatch import MonkeyPatch

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.files import File, FileList, FilesAPI
from deepset_cloud_sdk.api.upload_sessions import (
    UploadSession,
    UploadSessionIngestionStatus,
    UploadSessionStatus,
    WriteMode,
)
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile, FilesService


@pytest.fixture
def file_service(mocked_upload_sessions_api: Mock, mocked_files_api: Mock, mocked_s3: Mock) -> FilesService:
    return FilesService(upload_sessions=mocked_upload_sessions_api, files=mocked_files_api, s3=mocked_s3)


@pytest.mark.asyncio
class TestUploadsFileService:
    class TestFilePathsUpload:
        async def test_upload_file_paths(
            self,
            file_service: FilesService,
            mocked_upload_sessions_api: Mock,
            upload_session_response: UploadSession,
            mocked_s3: Mock,
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
                workspace_name="test_workspace",
                file_paths=[Path("./tmp/my-file")],
                write_mode=WriteMode.OVERWRITE,
                blocking=True,
                timeout_s=300,
            )

            mocked_upload_sessions_api.create.assert_called_once_with(
                workspace_name="test_workspace", write_mode=WriteMode.OVERWRITE
            )

            mocked_s3.upload_files_from_paths.assert_called_once_with(
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

    class TestFolderUpload:
        async def test_upload_folder_path(
            self,
            file_service: FilesService,
            monkeypatch: MonkeyPatch,
        ) -> None:
            mocked_upload_file_paths = AsyncMock(return_value=None)
            monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
            await file_service.upload_folder(
                workspace_name="test_workspace",
                folder_path=Path("./tests/data/upload_folder"),
                blocking=True,
                timeout_s=300,
            )
            assert mocked_upload_file_paths.called
            assert "test_workspace" == mocked_upload_file_paths.call_args[1]["workspace_name"]
            assert mocked_upload_file_paths.call_args[1]["blocking"] == True
            assert 300 == mocked_upload_file_paths.call_args[1]["timeout_s"]

            assert (
                Path("tests/data/upload_folder/example.txt.meta.json")
                in mocked_upload_file_paths.call_args[1]["file_paths"]
            )
            assert Path("tests/data/upload_folder/example.txt") in mocked_upload_file_paths.call_args[1]["file_paths"]
            assert Path("tests/data/upload_folder/example.pdf") in mocked_upload_file_paths.call_args[1]["file_paths"]

    class TestUploadTexts:
        async def test_upload_texts(
            self,
            file_service: FilesService,
            mocked_upload_sessions_api: Mock,
            upload_session_response: UploadSession,
            mocked_s3: Mock,
        ) -> None:
            dc_files = [
                DeepsetCloudFile(
                    name="test_file.txt",
                    text="test content",
                    meta={"test": "test"},
                )
            ]
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
            await file_service.upload_texts(
                workspace_name="test_workspace",
                dc_files=dc_files,
                write_mode=WriteMode.OVERWRITE,
                blocking=True,
                timeout_s=300,
            )

            mocked_upload_sessions_api.create.assert_called_once_with(
                workspace_name="test_workspace", write_mode=WriteMode.OVERWRITE
            )

            mocked_s3.upload_texts.assert_called_once_with(upload_session=upload_session_response, dc_files=dc_files)

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


@pytest.mark.asyncio
class TestListFilesService:
    async def test_list_all_files(self, file_service: FilesService, monkeypatch: MonkeyPatch) -> None:
        mocked_list_paginated = AsyncMock(
            side_effect=[
                FileList(
                    total=11,
                    data=[
                        File(
                            file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                            name="silly_things_1.txt",
                            size=611,
                            created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                            meta={},
                        )
                    ],
                    has_more=True,
                ),
                FileList(
                    total=11,
                    data=[
                        File(
                            file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                            name="silly_things_2.txt",
                            size=611,
                            created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                            meta={},
                        )
                    ],
                    has_more=False,
                ),
            ]
        )

        monkeypatch.setattr(file_service._files, "list_paginated", mocked_list_paginated)

        file_batches: List[List[File]] = []
        async for file_batch in file_service.list_all(workspace_name="test_workspace", batch_size=10, timeout_s=2):
            file_batches.append(file_batch)

        assert len(file_batches) > 0
        assert len(file_batches[0]) == 1
        assert file_batches[0][0] == File(
            file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
            name="silly_things_1.txt",
            size=611,
            meta={},
            created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
        )
        assert len(file_batches[1]) == 1
        assert file_batches[1][0] == File(
            file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
            name="silly_things_2.txt",
            size=611,
            meta={},
            created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
        )

    async def test_list_all_files_with_timeout(self, file_service: FilesService, monkeypatch: MonkeyPatch) -> None:
        mocked_list_paginated = AsyncMock(
            return_value=FileList(
                total=11,
                data=[
                    File(
                        file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                        url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                        name="silly_things_1.txt",
                        size=611,
                        created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                        meta={},
                    )
                ],
                has_more=True,
            )
        )
        monkeypatch.setattr(file_service._files, "list_paginated", mocked_list_paginated)
        with pytest.raises(TimeoutError):
            async for _ in file_service.list_all(workspace_name="test_workspace", batch_size=10, timeout_s=0):
                pass
