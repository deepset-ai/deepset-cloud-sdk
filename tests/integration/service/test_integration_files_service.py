import os
from pathlib import Path

import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import FilesService
from deepset_cloud_sdk.s3.upload import S3
from os import listdir
from os.path import isfile, join


@pytest.fixture
def workspace_name() -> str:
    return "sdk_write"


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            test_data_path = "./tests/test_data/msmarco.10"
            filepaths = [
                join(test_data_path, f)
                for f in listdir(test_data_path)
                if f.endswith(".txt") or f.endswith(".meta.json")
            ]
            await file_service.upload_file_paths(
                workspace_name=workspace_name,
                file_paths=filepaths,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )
