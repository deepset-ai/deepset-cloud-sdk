from pathlib import Path

import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import FilesService


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(self, integration_config: CommonConfig) -> None:
        # TODO: replace aws with actual aws client
        async with FilesService.factory(integration_config) as file_service:
            await file_service.upload_file_paths(
                workspace_name="sdk",
                file_paths=[Path("./tmp/my-file")],
                write_mode=WriteMode.OVERWRITE,
                blocking=False,  # dont wait for files to be ingested
            )
