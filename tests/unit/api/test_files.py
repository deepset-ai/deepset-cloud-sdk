import datetime
from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest

from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.files import File, FileList, FilesAPI


@pytest.fixture
def files_api(mocked_deepset_cloud_api: Mock) -> FilesAPI:
    return FilesAPI(mocked_deepset_cloud_api)


@pytest.mark.asyncio
class TestUtilitiesFilesAPI:
    pass


@pytest.mark.asyncio
class TestListFiles:
    async def test_list_paginated(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.get.return_value = httpx.Response(
            status_code=httpx.codes.OK,
            json={
                "total": 1,
                "data": [
                    {
                        "file_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                        "url": "/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                        "name": "silly_things_1.txt",
                        "size": 611,
                        "characters": 0,
                        "meta": {},
                        "created_at": "2022-06-21T16:40:00.634653+00:00",
                        "languages": None,
                    }
                ],
                "has_more": False,
            },
        )
        result = await files_api.list_paginated(
            workspace_name="test_workspace",
            limit=10,
            name="things_1",
            content="silly",
            odata_filter="created_at eq '2022-06-21T16:40:00.634653+00:00' ",
        )
        assert result == FileList(
            total=1,
            data=[
                File(
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
                    name="silly_things_1.txt",
                    size=611,
                    meta={},
                    created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
                )
            ],
            has_more=False,
        )
