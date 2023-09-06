import os
import tempfile
from pathlib import Path
from typing import List

import pytest

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import WriteMode
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile, FilesService


@pytest.fixture
def workspace_name() -> str:
    return "sdk_write"


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            timeout = 120 if "dev.cloud.dpst.dev" in integration_config.api_url else 300

            result = await file_service.upload(
                workspace_name=workspace_name,
                paths=[Path("./tests/test_data/msmarco.10")],
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=timeout,
            )
            assert result.total_files == 20
            assert result.successful_upload_count == 20
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

    async def test_upload_texts(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            files = [
                DeepsetCloudFile("file1", "file1.txt", {"which": 1}),
                DeepsetCloudFile("file2", "file2.txt", {"which": 2}),
                DeepsetCloudFile("file3", "file3.txt", {"which": 3}),
                DeepsetCloudFile("file4", "file4.txt", {"which": 4}),
                DeepsetCloudFile("file5", "file5.txt", {"which": 5}),
            ]
            result = await file_service.upload_texts(
                workspace_name=workspace_name,
                files=files,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )
            assert result.total_files == 10
            assert result.successful_upload_count == 10
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0


@pytest.mark.asyncio
class TestListFilesService:
    async def test_list_all_files(self, integration_config: CommonConfig) -> None:
        async with FilesService.factory(integration_config) as file_service:
            file_batches: List[List[File]] = []
            async for file_batch in file_service.list_all(
                workspace_name="sdk_read",
                batch_size=11,
                timeout_s=120,
            ):
                file_batches.append(file_batch)

            assert len(file_batches) >= 2
            assert len(file_batches[0]) == 11
            assert len(file_batches[1]) >= 1


@pytest.mark.asyncio
class TestDownloadFilesService:
    async def test_download_files(self, integration_config: CommonConfig) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            async with FilesService.factory(integration_config) as file_service:
                # cancel download after 5 seconds
                try:
                    await file_service.download(workspace_name="sdk_read", file_dir=tmp_dir, timeout_s=5)
                finally:
                    # test that files were downloaded
                    assert len(os.listdir(tmp_dir)) > 0
