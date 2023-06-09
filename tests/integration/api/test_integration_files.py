import pytest

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.files import FilesAPI


@pytest.fixture
def workspace_name() -> str:
    return "sdk_read"


@pytest.mark.asyncio
class TestListFiles:
    async def test_list_paginated(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with DeepsetCloudAPI.factory(integration_config) as deepset_cloud_api:
            files_api = FilesAPI(deepset_cloud_api)
            result = await files_api.list_paginated(
                workspace_name=workspace_name, limit=10, name="Seven", content="HBO's", odata_filter="find eq 'me'"
            )

            assert result.total == 1
            assert result.has_more is False
            assert len(result.data) == 1
            found_file = result.data[0]
            assert found_file.name == "20_Light_of_the_Seven.txt"
            assert found_file.size == 5044
            assert found_file.meta == {"find": "me"}
