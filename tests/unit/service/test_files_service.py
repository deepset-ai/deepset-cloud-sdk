import datetime
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from _pytest.monkeypatch import MonkeyPatch

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.files import File, FileList
from deepset_cloud_sdk._api.upload_sessions import (
    UploadSession,
    UploadSessionDetail,
    UploadSessionDetailList,
    UploadSessionIngestionStatus,
    UploadSessionStatus,
    UploadSessionStatusEnum,
    UploadSessionWriteModeEnum,
    WriteMode,
)
from deepset_cloud_sdk._s3.upload import S3UploadSummary
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile, FilesService
from deepset_cloud_sdk.models import UserInfo


@pytest.fixture
def file_service(mocked_upload_sessions_api: Mock, mocked_files_api: Mock, mocked_s3: Mock) -> FilesService:
    return FilesService(upload_sessions=mocked_upload_sessions_api, files=mocked_files_api, s3=mocked_s3)


@pytest.mark.asyncio
class TestFilePathsUpload:
    async def test_upload_file_paths(
        self,
        file_service: FilesService,
        mocked_upload_sessions_api: Mock,
        upload_session_response: UploadSession,
        mocked_s3: Mock,
    ) -> None:
        upload_summary = S3UploadSummary(total_files=1, successful_upload_count=1, failed_upload_count=0, failed=[])
        mocked_s3.upload_files_from_paths.return_value = upload_summary
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
        result = await file_service.upload_file_paths(
            workspace_name="test_workspace",
            file_paths=[Path("./tmp/my-file")],
            write_mode=WriteMode.OVERWRITE,
            blocking=True,
            timeout_s=300,
        )
        assert result == upload_summary

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


@pytest.mark.asyncio
class TestUpload:
    async def test_upload_paths_to_folder(
        self,
        file_service: FilesService,
        monkeypatch: MonkeyPatch,
    ) -> None:
        mocked_upload_file_paths = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
        await file_service.upload(
            workspace_name="test_workspace",
            paths=[Path("./tests/data/upload_folder")],
            blocking=True,
            timeout_s=300,
        )
        assert mocked_upload_file_paths.called
        assert "test_workspace" == mocked_upload_file_paths.call_args[1]["workspace_name"]
        assert mocked_upload_file_paths.call_args[1]["blocking"] is True
        assert 300 == mocked_upload_file_paths.call_args[1]["timeout_s"]

        assert (
            Path("tests/data/upload_folder/example.txt.meta.json")
            in mocked_upload_file_paths.call_args[1]["file_paths"]
        )
        assert Path("tests/data/upload_folder/example.txt") in mocked_upload_file_paths.call_args[1]["file_paths"]
        assert Path("tests/data/upload_folder/example.pdf") in mocked_upload_file_paths.call_args[1]["file_paths"]

    async def test_upload_paths_nested(
        self,
        file_service: FilesService,
        monkeypatch: MonkeyPatch,
    ) -> None:
        mocked_upload_file_paths = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
        await file_service.upload(
            workspace_name="test_workspace",
            paths=[Path("./tests/data/upload_folder_nested")],
            blocking=True,
            timeout_s=300,
            recursive=True,
        )
        assert mocked_upload_file_paths.called

        assert (
            Path("tests/data/upload_folder_nested/nested_folder/second.txt")
            in mocked_upload_file_paths.call_args[1]["file_paths"]
        )
        assert (
            Path("tests/data/upload_folder_nested/example.txt") in mocked_upload_file_paths.call_args[1]["file_paths"]
        )

        assert (
            Path("tests/data/upload_folder_nested/meta/example.txt.meta.json")
            in mocked_upload_file_paths.call_args[1]["file_paths"]
        )

    async def test_upload_paths_to_file(
        self,
        file_service: FilesService,
        monkeypatch: MonkeyPatch,
    ) -> None:
        mocked_upload_file_paths = AsyncMock(return_value=None)
        monkeypatch.setattr(FilesService, "upload_file_paths", mocked_upload_file_paths)
        await file_service.upload(
            workspace_name="test_workspace",
            paths=[Path("./tests/data/upload_folder/example.txt")],
            blocking=True,
            timeout_s=300,
            recursive=True,
        )
        assert mocked_upload_file_paths.called
        assert len(mocked_upload_file_paths.call_args[1]["file_paths"]) == 1

        assert Path("tests/data/upload_folder/example.txt") in mocked_upload_file_paths.call_args[1]["file_paths"]


@pytest.mark.asyncio
class TestUploadTexts:
    async def test_upload_texts(
        self,
        file_service: FilesService,
        mocked_upload_sessions_api: Mock,
        upload_session_response: UploadSession,
        mocked_s3: Mock,
    ) -> None:
        upload_summary = S3UploadSummary(total_files=1, successful_upload_count=1, failed_upload_count=0, failed=[])
        mocked_s3.upload_texts.return_value = upload_summary
        files = [
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
        result = await file_service.upload_texts(
            workspace_name="test_workspace",
            files=files,
            write_mode=WriteMode.OVERWRITE,
            blocking=True,
            timeout_s=300,
            show_progress=False,
        )
        assert result == upload_summary

        mocked_upload_sessions_api.create.assert_called_once_with(
            workspace_name="test_workspace", write_mode=WriteMode.OVERWRITE
        )

        mocked_s3.upload_texts.assert_called_once_with(
            upload_session=upload_session_response, files=files, show_progress=False
        )

        mocked_upload_sessions_api.close.assert_called_once_with(
            workspace_name="test_workspace", session_id=upload_session_response.session_id
        )
        mocked_upload_sessions_api.status.assert_called_once_with(
            workspace_name="test_workspace", session_id=upload_session_response.session_id
        )


@pytest.mark.asyncio
async def test_upload_file_paths_with_timeout(
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

    async def test_list_all_files_with_no_results(self, file_service: FilesService, monkeypatch: MonkeyPatch) -> None:
        mocked_list_paginated = AsyncMock(
            side_effect=[
                FileList(
                    total=11,
                    data=[],
                    has_more=True,
                )
            ]
        )

        monkeypatch.setattr(file_service._files, "list_paginated", mocked_list_paginated)

        file_batches: List[List[File]] = []
        async for file_batch in file_service.list_all(workspace_name="test_workspace", batch_size=10, timeout_s=2):
            file_batches.append(file_batch)

        assert file_batches == []

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


@pytest.mark.asyncio
class TestListUploadSessionService:
    async def test_list_all_upload_sessions_files(self, file_service: FilesService, monkeypatch: MonkeyPatch) -> None:
        mocked_list_paginated = AsyncMock(
            side_effect=[
                UploadSessionDetailList(
                    total=2,
                    has_more=True,
                    data=[
                        UploadSessionDetail(
                            session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            created_by=UserInfo(
                                user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                                given_name="Fake",
                                family_name="User",
                            ),
                            expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                            created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                            write_mode=UploadSessionWriteModeEnum.KEEP,
                            status=UploadSessionStatusEnum.OPEN,
                        )
                    ],
                ),
                UploadSessionDetailList(
                    total=2,
                    has_more=False,
                    data=[
                        UploadSessionDetail(
                            session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            created_by=UserInfo(
                                user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                                given_name="Fake",
                                family_name="User",
                            ),
                            expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                            created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                            write_mode=UploadSessionWriteModeEnum.KEEP,
                            status=UploadSessionStatusEnum.OPEN,
                        )
                    ],
                ),
                UploadSessionDetailList(
                    total=2,
                    has_more=False,
                    data=[],
                ),
            ]
        )

        monkeypatch.setattr(file_service._upload_sessions, "list", mocked_list_paginated)

        upload_session_batches: List[List[UploadSessionDetail]] = []
        async for file_batch in file_service.list_upload_sessions(
            workspace_name="test_workspace", batch_size=10, timeout_s=2
        ):
            upload_session_batches.append(file_batch)

        assert len(upload_session_batches) > 0
        assert len(upload_session_batches[0]) == 1
        assert upload_session_batches[0][0] == UploadSessionDetail(
            session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            created_by=UserInfo(
                user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                given_name="Fake",
                family_name="User",
            ),
            expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
            created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
            write_mode=UploadSessionWriteModeEnum.KEEP,
            status=UploadSessionStatusEnum.OPEN,
        )
        assert len(upload_session_batches[1]) == 1
        assert upload_session_batches[1][0] == UploadSessionDetail(
            session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            created_by=UserInfo(
                user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                given_name="Fake",
                family_name="User",
            ),
            expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
            created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
            write_mode=UploadSessionWriteModeEnum.KEEP,
            status=UploadSessionStatusEnum.OPEN,
        )

    async def test_list_all_upload_sessions_with_no_results(
        self, file_service: FilesService, monkeypatch: MonkeyPatch
    ) -> None:
        mocked_list_paginated = AsyncMock(
            side_effect=[
                UploadSessionDetailList(
                    total=0,
                    has_more=False,
                    data=[],
                ),
            ]
        )

        monkeypatch.setattr(file_service._upload_sessions, "list", mocked_list_paginated)

        upload_session_batches: List[List[UploadSessionDetail]] = []
        async for file_batch in file_service.list_upload_sessions(
            workspace_name="test_workspace", batch_size=10, timeout_s=2
        ):
            upload_session_batches.append(file_batch)

        assert upload_session_batches == []

    async def test_list_all_upload_sessions_with_timeout(
        self, file_service: FilesService, monkeypatch: MonkeyPatch
    ) -> None:
        mocked_list_paginated = AsyncMock(
            return_value=UploadSessionDetailList(
                total=2,
                has_more=True,
                data=[
                    UploadSessionDetail(
                        session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                        created_by=UserInfo(
                            user_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                            given_name="Fake",
                            family_name="User",
                        ),
                        expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                        created_at=datetime.datetime.fromisoformat("2022-06-21T16:10:00.634653+00:00"),
                        write_mode=UploadSessionWriteModeEnum.KEEP,
                        status=UploadSessionStatusEnum.OPEN,
                    )
                ],
            )
        )

        monkeypatch.setattr(file_service._upload_sessions, "list", mocked_list_paginated)

        with pytest.raises(TimeoutError):
            async for _ in file_service.list_upload_sessions(
                workspace_name="test_workspace", batch_size=10, timeout_s=0
            ):
                pass


@pytest.mark.asyncio
class TestGetUploadSessionStatusService:
    async def test_get_upload_session(self, file_service: FilesService, monkeypatch: MonkeyPatch) -> None:
        returned_upload_session_status = UploadSessionStatus(
            session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            expires_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
            documentation_url="https://docs.deepset.ai",
            ingestion_status=UploadSessionIngestionStatus(
                failed_files=0,
                finished_files=1,
            ),
        )
        mocked_list_paginated = AsyncMock(return_value=returned_upload_session_status)

        monkeypatch.setattr(file_service._upload_sessions, "status", mocked_list_paginated)

        upload_session_status = await file_service.get_upload_session(
            workspace_name="test_workspace", session_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")
        )
        assert upload_session_status == returned_upload_session_status


@pytest.mark.asyncio
class TestValidateFilePaths:
    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/file1.txt"), Path("/home/user/file2.txt")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths(self, file_paths: List[Path]) -> None:
        FilesService._validate_file_paths(file_paths)

    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/.DS_Store")],
            [Path("/home/user/file2.json")],
            [Path("/home/user/file1.md")],
            [Path("/home/user/file1.docx")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file2.pdf.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths_with_broken_meta_field(self, file_paths: List[Path]) -> None:
        with pytest.raises(ValueError):
            FilesService._validate_file_paths(file_paths)


class TestPreprocessFiles:
    def test_show_progress_triggers_spinner_update(self) -> None:
        mock_spinner = Mock()
        mock_spinner.text = "initial"

        FilesService._preprocess_paths([Path("tests/data/upload_folder/example.txt")], spinner=mock_spinner)

        assert mock_spinner.text == "Validating files and metadata."

    def test_no_spinner_does_not_cause_error(self) -> None:
        try:
            FilesService._preprocess_paths([Path("tests/data/upload_folder/example.txt")], spinner=None)
        except Exception as e:
            assert False, f"No error should have been thrown but got error of type '{type(e).__name__}'"
