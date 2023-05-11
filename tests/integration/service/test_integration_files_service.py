from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import UploadSessionsAPI
from deepset_cloud_sdk.service.files_service import FilesService


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(self, integration_config: CommonConfig) -> None:
        # TODO: replace aws with actual aws client
        async with FilesService.factory(integration_config) as file_service:
            await file_service.upload_file_paths(
                workspace_name="sdk",
                file_paths=[Path("./tmp/my-file")],
                blocking=False,  # dont wait for files to be ingested
            )
