import os
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import UploadSessionsAPI
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
        # TODO: replace aws with actual aws client
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            files_api = FilesAPI(deepset_cloud_api)
            upload_sessions_api = UploadSessionsAPI(deepset_cloud_api)
            s3 = S3(concurrency=1)
            file_service = FilesService(upload_sessions_api, files_api, s3)
            test_data_path = "./tests/test_data/msmarco.10"
            filepaths = [
                join(test_data_path, f)
                for f in listdir(test_data_path)
                if f.endswith(".txt") or f.endswith(".meta.json")
            ]
            await file_service.upload_file_paths(
                workspace_name=workspace_name,
                file_paths=filepaths,
                blocking=True,  # wait for files to be ingested
                timeout_s=30,
            )
