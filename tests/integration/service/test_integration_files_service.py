import os
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import List

import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.s3.upload import S3
from deepset_cloud_sdk.service.files_service import DeepsetCloudFile, FilesService


@pytest.fixture
def workspace_name() -> str:
    return "sdk_write"


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            test_data_path = "./tests/test_data/msmarco.10"
            file_paths = [
                Path(join(test_data_path, f))
                for f in listdir(test_data_path)
                if f.endswith(".txt") or f.endswith(".meta.json")
            ]
            await file_service.upload_file_paths(
                workspace_name=workspace_name,
                file_paths=file_paths,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )

    async def test_upload_texts(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            dc_files = [
                DeepsetCloudFile("file1", "file1.txt", {"which": 1}),
                DeepsetCloudFile("file2", "file2.txt", {"which": 2}),
                DeepsetCloudFile("file3", "file3.txt", {"which": 3}),
                DeepsetCloudFile("file4", "file4.txt", {"which": 4}),
                DeepsetCloudFile("file5", "file5.txt", {"which": 5}),
            ]
            await file_service.upload_texts(
                workspace_name=workspace_name,
                dc_files=dc_files,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )


@pytest.mark.asyncio
class TestListFilesService:
    async def test_list_all_files(self, integration_config: CommonConfig) -> None:
        async with FilesService.factory(integration_config) as file_service:
            file_batches: List[List[File]] = []
            async for file_batch in file_service.list_all(
                workspace_name="sdk_read",
                batch_size=11,
            ):
                file_batches.append(file_batch)

            assert len(file_batches) == 2
            assert len(file_batches[0]) == 11
            assert len(file_batches[1]) == 9
