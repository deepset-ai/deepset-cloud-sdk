from typing import List
from unittest.mock import Mock

import httpx
import pytest

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import File, FilesAPI


@pytest.mark.asyncio
class TestListFiles:
    async def test_list_paginated(self, integration_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            files_api = FilesAPI(deepset_cloud_api)

            result = await files_api.list_paginated(
                workspace_name="sdk",
                limit=10,
                name="Seven",
                content="HBO's",
            )

            assert result.total == 1
            assert result.has_more == False
            assert len(result.data) == 1
            found_file = result.data[0]
            assert found_file.name == "20_Light_of_the_Seven.txt"
            assert found_file.size == 5044
            assert found_file.meta == {}

    async def test_list_all_files(self, integration_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(integration_config, client=client)
            files_api = FilesAPI(deepset_cloud_api)

            file_batches: List[List[File]] = []
            async for file_batch in files_api.list_all(
                workspace_name="sdk",
                batch_size=11,
            ):
                file_batches.append(file_batch)

            assert len(file_batches) == 2
            assert len(file_batches[0]) == 11
            assert len(file_batches[1]) == 9
