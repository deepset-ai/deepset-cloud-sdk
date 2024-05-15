import datetime
import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import ANY, Mock
from uuid import UUID

import httpx
import pytest

from deepset_cloud_sdk._api.files import (
    FailedToUploadFileException,
    File,
    FileList,
    FileNotFoundInDeepsetCloudException,
    FilesAPI,
    NotMatchingFileTypeException,
)
from deepset_cloud_sdk._api.upload_sessions import WriteMode


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
            with pytest.raises(FileNotFoundInDeepsetCloudException):
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
            with pytest.raises(FileNotFoundInDeepsetCloudException):
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


@pytest.mark.asyncio
class TestDirectUploadFilePath:
    @pytest.mark.parametrize("error_code", [httpx.codes.NOT_FOUND, httpx.codes.SERVICE_UNAVAILABLE])
    async def test_direct_upload_file_failed(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock, error_code: int
    ) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=error_code,
        )
        with pytest.raises(FailedToUploadFileException):
            await files_api.direct_upload_path(
                workspace_name="test_workspace",
                file_path=Path("./tests/test_data/basic.txt"),
                meta={},
            )

    async def test_direct_upload_file(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=httpx.codes.CREATED,
            json={"file_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10"},
        )
        file_id = await files_api.direct_upload_path(
            workspace_name="test_workspace",
            file_path=Path("./tests/test_data/basic.txt"),
            meta={"key": "value"},
            write_mode=WriteMode.OVERWRITE,
        )
        assert file_id == UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")
        mocked_deepset_cloud_api.post.assert_called_once_with(
            "test_workspace",
            "files",
            files={"file": ("basic.txt", ANY), "meta": (None, '{"key": "value"}')},
            params={
                "write_mode": "OVERWRITE",
            },
        )

    async def test_direct_upload_file_with_name(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=httpx.codes.CREATED,
            json={"file_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10"},
        )
        file_id = await files_api.direct_upload_path(
            workspace_name="test_workspace",
            file_path=Path("./tests/test_data/basic.txt"),
            meta={"key": "value"},
            file_name="my_file.txt",
            write_mode=WriteMode.OVERWRITE,
        )
        assert file_id == UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")
        mocked_deepset_cloud_api.post.assert_called_once_with(
            "test_workspace",
            "files",
            files={"file": ("my_file.txt", ANY), "meta": (None, '{"key": "value"}')},
            params={"write_mode": "OVERWRITE"},
        )

    async def test_direct_upload_with_path_as_string(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=httpx.codes.CREATED,
            json={"file_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10"},
        )
        file_id = await files_api.direct_upload_path(
            workspace_name="test_workspace",
            file_path="./tests/test_data/basic.txt",
            meta={"key": "value"},
            file_name="my_file.txt",
            write_mode=WriteMode.FAIL,
        )
        assert file_id == UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")
        mocked_deepset_cloud_api.post.assert_called_once_with(
            "test_workspace",
            "files",
            files={"file": ("my_file.txt", ANY), "meta": (None, '{"key": "value"}')},
            params={"write_mode": "FAIL"},
        )


@pytest.mark.asyncio
class TestDirectUploadText:
    async def test_direct_upload_file_for_wrong_file_type_name(self, files_api: FilesAPI) -> None:
        with pytest.raises(NotMatchingFileTypeException):
            await files_api.direct_upload_in_memory(
                workspace_name="test_workspace",
                file_name="basic.xls",
                content=b"some text",
                meta={},
            )

    @pytest.mark.parametrize("error_code", [httpx.codes.NOT_FOUND, httpx.codes.SERVICE_UNAVAILABLE])
    async def test_direct_upload_file_failed(
        self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock, error_code: int
    ) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=error_code,
        )
        with pytest.raises(FailedToUploadFileException):
            await files_api.direct_upload_in_memory(
                workspace_name="test_workspace",
                file_name="basic.txt",
                content=b"some text",
                meta={},
            )

    async def test_direct_upload_file(self, files_api: FilesAPI, mocked_deepset_cloud_api: Mock) -> None:
        mocked_deepset_cloud_api.post.return_value = httpx.Response(
            status_code=httpx.codes.CREATED,
            json={"file_id": "cd16435f-f6eb-423f-bf6f-994dc8a36a10"},
        )
        file_id = await files_api.direct_upload_in_memory(
            workspace_name="test_workspace",
            file_name="basic.txt",
            content=b"some text",
            meta={"key": "value"},
            write_mode=WriteMode.OVERWRITE,
        )
        assert file_id == UUID("cd16435f-f6eb-423f-bf6f-994dc8a36a10")
        mocked_deepset_cloud_api.post.assert_called_once_with(
            "test_workspace",
            "files",
            files={"file": ("basic.txt", b"some text")},
            data={"meta": json.dumps({"key": "value"})},
            params={"write_mode": "OVERWRITE"},
        )
