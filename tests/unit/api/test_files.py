import datetime
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest

from deepset_cloud_sdk._api.files import File, FileList, FileNotFound, FilesAPI


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
        mocked_deepset_cloud_api.get.assert_called_once_with(
            "test_workspace",
            "files",
            params={
                "limit": 10,
                "name": "things_1",
                "content": "silly",
                "filter": "created_at eq '2022-06-21T16:40:00.634653+00:00' ",
            },
        )


@pytest.mark.asyncio
class TestDownloadFile:
    async def test_download_file_not_found(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mocked_deepset_cloud_api.get.return_value = httpx.Response(
                status_code=httpx.codes.NOT_FOUND,
            )
            with pytest.raises(FileNotFound):
                await files_api.download(
                    workspace_name="test_workspace",
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    file_name="silly_things_1.txt",
                    include_meta=False,
                    file_dir=Path(tmp_dir),
                )

    async def test_download_file_with_unexpected_error(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mocked_deepset_cloud_api.get.return_value = httpx.Response(
                status_code=httpx.codes.SERVICE_UNAVAILABLE,
            )
            with pytest.raises(Exception):
                await files_api.download(
                    workspace_name="test_workspace",
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    file_name="silly_things_1.txt",
                    include_meta=False,
                    file_dir=Path(tmp_dir),
                )

    async def test_download(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mocked_deepset_cloud_api.get.return_value = httpx.Response(
                status_code=httpx.codes.OK,
                content=b"some content",
            )
            await files_api.download(
                workspace_name="test_workspace",
                file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                file_name="silly_things_1.txt",
                include_meta=False,
                file_dir=Path(tmp_dir),
            )
            with Path.open(Path(tmp_dir + "/silly_things_1.txt"), encoding="UTF-8") as file:
                assert file.read() == "some content"

            mocked_deepset_cloud_api.get.assert_called_once_with(
                "test_workspace", "files/cd16435f-f6eb-423f-bf6f-994dc8a36a10"
            )

    async def test_download_with_metadata(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:

            def mock_response(*args: Any, **kwargs: Any) -> httpx.Response:
                if args[1] == "files/cd16435f-f6eb-423f-bf6f-994dc8a36a10":
                    # Return a different response if include_meta is True
                    return httpx.Response(
                        status_code=httpx.codes.OK,
                        content=b"some content",
                    )
                return httpx.Response(
                    status_code=httpx.codes.OK,
                    json={"key": "value"},
                )

            mocked_deepset_cloud_api.get.side_effect = mock_response

            await files_api.download(
                workspace_name="test_workspace",
                file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                file_name="silly_things_1.txt",
                include_meta=True,
                file_dir=Path(tmp_dir),
            )
            with Path.open(Path(tmp_dir + "/silly_things_1.txt"), encoding="UTF-8") as file:
                assert file.read() == "some content"

            with Path.open(Path(tmp_dir + "/silly_things_1.txt.meta.json"), encoding="UTF-8") as file:
                assert file.read() == '{"key": "value"}'
            assert mocked_deepset_cloud_api.get.call_count == 2

    async def test_download_with_metadata_file_not_found(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:

            def mock_response(*args: Any, **kwargs: Any) -> httpx.Response:
                if args[1] == "files/cd16435f-f6eb-423f-bf6f-994dc8a36a10":
                    # Return a different response if include_meta is True
                    return httpx.Response(
                        status_code=httpx.codes.OK,
                        content=b"some content",
                    )
                return httpx.Response(
                    status_code=httpx.codes.NOT_FOUND,
                    json={"key": "value"},
                )

            mocked_deepset_cloud_api.get.side_effect = mock_response
            with pytest.raises(FileNotFound):
                await files_api.download(
                    workspace_name="test_workspace",
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    file_name="silly_things_1.txt",
                    include_meta=True,
                    file_dir=Path(tmp_dir),
                )

    async def test_download_with_metadata_unexpected_error(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:

            def mock_response(*args: Any, **kwargs: Any) -> httpx.Response:
                if args[1] == "files/cd16435f-f6eb-423f-bf6f-994dc8a36a10":
                    # Return a different response if include_meta is True
                    return httpx.Response(
                        status_code=httpx.codes.OK,
                        content=b"some content",
                    )
                return httpx.Response(
                    status_code=httpx.codes.SERVICE_UNAVAILABLE,
                    json={"key": "value"},
                )

            mocked_deepset_cloud_api.get.side_effect = mock_response
            with pytest.raises(Exception):
                await files_api.download(
                    workspace_name="test_workspace",
                    file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                    file_name="silly_things_1.txt",
                    include_meta=True,
                    file_dir=Path(tmp_dir),
                )

    async def test_download_file_with_name_collsion_for_raw_file(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with Path.open(Path(tmp_dir) / "silly_things_1.txt", "wb") as file:
                file.write("first content".encode("UTF-8"))

            with Path.open(Path(tmp_dir) / "silly_things_1_1.txt", "wb") as file:
                file.write("second content".encode("UTF-8"))

            mocked_deepset_cloud_api.get.return_value = httpx.Response(
                status_code=httpx.codes.OK,
                content=b"third content",
            )

            await files_api.download(
                workspace_name="test_workspace",
                file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                file_name="silly_things_1.txt",
                include_meta=False,
                file_dir=Path(tmp_dir),
            )
            with Path.open(Path(tmp_dir + "/silly_things_1.txt"), encoding="UTF-8") as file:
                assert file.read() == "first content"

            with Path.open(Path(tmp_dir + "/silly_things_1_1.txt"), encoding="UTF-8") as file:
                assert file.read() == "second content"

            # check that the new file is stored with the suffix `_1` and has the new content
            with Path.open(Path(tmp_dir + "/silly_things_1_2.txt"), encoding="UTF-8") as file:
                assert file.read() == "third content"

    async def test_download_file_with_name_collsion_matches_metadata(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with Path.open(Path(tmp_dir) / "silly_things_1.txt", "wb") as file:
                file.write("first content".encode("UTF-8"))

            with Path.open(Path(tmp_dir) / "silly_things_1_1.txt", "wb") as file:
                file.write("second content".encode("UTF-8"))

            def mock_response(*args: Any, **kwargs: Any) -> httpx.Response:
                if args[1] == "files/cd16435f-f6eb-423f-bf6f-994dc8a36a10":
                    # Return a different response if include_meta is True
                    return httpx.Response(
                        status_code=httpx.codes.OK,
                        content=b"third content",
                    )
                return httpx.Response(
                    status_code=httpx.codes.OK,
                    json={"key": "value"},
                )

            mocked_deepset_cloud_api.get.side_effect = mock_response
            await files_api.download(
                workspace_name="test_workspace",
                file_id=UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10"),
                file_name="silly_things_1.txt",
                include_meta=True,
                file_dir=Path(tmp_dir),
            )
            with Path.open(Path(tmp_dir + "/silly_things_1.txt")) as _file:
                assert _file.read() == "first content"

            with Path.open(Path(tmp_dir + "/silly_things_1_1.txt")) as _file:
                assert _file.read() == "second content"

            # check that the new file is stored with the suffix `_1` and has the new content
            with Path.open(Path(tmp_dir + "/silly_things_1_2.txt")) as _file:
                assert _file.read() == "third content"

            with Path.open(Path(tmp_dir + "/silly_things_1_2.txt.meta.json")) as _file:
                assert _file.read() == '{"key": "value"}'
