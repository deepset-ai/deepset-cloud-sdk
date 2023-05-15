from pathlib import Path
from typing import List

import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.files import File
from deepset_cloud_sdk.api.upload_sessions import WriteMode
from deepset_cloud_sdk.service.files_service import FilesService


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_upload_file_paths(self, integration_config: CommonConfig) -> None:
        # TODO: replace aws with actual aws client
        async with FilesService.factory(integration_config) as file_service:
            await file_service.upload_file_paths(
                workspace_name="sdk_read",
                file_paths=[Path("./tmp/my-file")],
                write_mode=WriteMode.OVERWRITE,
                blocking=False,  # dont wait for files to be ingested
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
