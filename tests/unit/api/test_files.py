import datetime
from typing import List
from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest

from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.api.files import File, FileList, FilesAPI


@pytest.fixture
def deepset_cloud_api() -> DeepsetCloudAPI:
    return Mock(spec=DeepsetCloudAPI)


@pytest.fixture
def files_api(deepset_cloud_api: DeepsetCloudAPI) -> FilesAPI:
    return FilesAPI(deepset_cloud_api)


@pytest.mark.asyncio
class TestUtilitiesFilesAPI:
    pass


@pytest.mark.asyncio
class TestListFiles:
    async def test_list_paginated(self, files_api: FilesAPI, deepset_cloud_api: Mock) -> None:
        deepset_cloud_api.get.return_value = httpx.Response(
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
            filter="created_at eq '2022-06-21T16:40:00.634653+00:00' ",
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

    async def test_list_all_files_with_timeout(self, files_api: FilesAPI, deepset_cloud_api: Mock) -> None:
        deepset_cloud_api.get.return_value = httpx.Response(
            status_code=httpx.codes.OK,
            json={
                "total": 11,
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
                "has_more": True,
            },
        )
        file_batches: List[List[File]] = []
        async for file_batch in files_api.list_all(workspace_name="test_workspace", batch_size=10, timeout=1):
            file_batches.append(file_batch)

        assert len(file_batches) > 0
        assert len(file_batches[0]) == 1
        assert file_batches[0][0] == File(
            file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
            url="/api/v1/workspaces/search tests/files/cd16435f-f6eb-423f-bf6f-994dc8a36a10",
            name="silly_things_1.txt",
            size=611,
            meta={},
            created_at=datetime.datetime.fromisoformat("2022-06-21T16:40:00.634653+00:00"),
        )
