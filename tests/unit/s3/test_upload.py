import asyncio
from pathlib import Path
from typing import List
from unittest.mock import Mock, mock_open, patch
from urllib.error import HTTPError

import aiohttp
import pytest
from tqdm.asyncio import tqdm

from deepset_cloud_sdk.api.upload_sessions import UploadSession, UploadSessionDetail
from deepset_cloud_sdk.models import DeepsetCloudFile
from deepset_cloud_sdk.s3.upload import S3, make_safe_file_name


class TestUploadsS3:
    class TestHelpers:
        @pytest.mark.parametrize(
            "input_file_name,expected_file_name",
            [
                ("hello.txt", "hello.txt"),
                # unprintable characters
                (
                    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F",
                    "_" * 32,
                ),
                # additional special characters
                ("""#%"'|<>{}`^[]~\\""", "_" * 15),
                ("$£%\x09宿 a.txt", "%24%C2%A3__%E5%AE%BF%20a.txt"),
            ],
        )
        def test_make_safe_file_name(self, input_file_name: str, expected_file_name: str) -> None:
            safe_name = make_safe_file_name(input_file_name)
            assert safe_name == expected_file_name

    @patch.object(aiohttp.ClientSession, "post")
    @pytest.mark.asyncio
    class TestS3:
        @patch.object(tqdm, "gather")
        async def test_upload_texts_with_progress(
            self, tqdm_gather: Mock, post: Mock, upload_session_response: UploadSession
        ) -> None:
            s3 = S3()
            files = [
                DeepsetCloudFile("one.txt", "one"),
                DeepsetCloudFile("two.txt", "two"),
                DeepsetCloudFile("three.txt", "three"),
            ]
            await s3.upload_texts(upload_session=upload_session_response, files=files, show_progress=True)

            assert tqdm_gather.call_count == 1

        async def test_upload_texts_with_progress_check_http_calls(
            self, post: Mock, upload_session_response: UploadSession
        ) -> None:
            s3 = S3()
            files = [
                DeepsetCloudFile("one.txt", "one"),
                DeepsetCloudFile("two.txt", "two"),
                DeepsetCloudFile("three.txt", "three"),
            ]
            await s3.upload_texts(upload_session=upload_session_response, files=files, show_progress=True)

            assert post.call_count == 3

        @patch.object(tqdm, "gather")
        async def test_upload_texts_without_progress(
            self, tqdm_gather: Mock, post: Mock, upload_session_response: UploadSession
        ) -> None:
            s3 = S3()
            files = [
                DeepsetCloudFile("one.txt", "one"),
                DeepsetCloudFile("two.txt", "two"),
                DeepsetCloudFile("three.txt", "three"),
            ]
            await s3.upload_texts(upload_session=upload_session_response, files=files, show_progress=False)

            assert tqdm_gather.call_count == 0

            assert post.call_count == 3

        async def test_upload_files_without_progress(self, post: Mock, upload_session_response: UploadSession) -> None:
            s3 = S3()

            files = [
                Path("./tests/test_data/msmarco.10/16675.txt"),
                Path("./tests/test_data/msmarco.10/16675.txt.meta.json"),
                Path("./tests/test_data/msmarco.10/22297.txt"),
                Path("./tests/test_data/msmarco.10/22297.txt.meta.json"),
                Path("./tests/test_data/msmarco.10/35887.txt"),
                Path("./tests/test_data/msmarco.10/35887.txt.meta.json"),
            ]

            results = await s3.upload_files_from_paths(upload_session_response, files)
            assert results.total_files == 6
            assert results.successful_upload_count == 6
            assert results.failed_upload_count == 0
            assert len(results.failed) == 0

        async def test_upload_files_from_path_http_error(self, upload_session_response: UploadSession) -> None:
            with patch.object(
                aiohttp.ClientSession, "post", side_effect=HTTPError("https://error.com", 503, "test error", "", None)  # type: ignore
            ):
                s3 = S3()

                files = [
                    Path("./tests/test_data/msmarco.10/16675.txt"),
                    Path("./tests/test_data/msmarco.10/16675.txt.meta.json"),
                    Path("./tests/test_data/msmarco.10/22297.txt"),
                    Path("./tests/test_data/msmarco.10/22297.txt.meta.json"),
                    Path("./tests/test_data/msmarco.10/35887.txt"),
                    Path("./tests/test_data/msmarco.10/35887.txt.meta.json"),
                ]

                results = await s3.upload_files_from_paths(upload_session_response, files)
                assert results.total_files == 6
                assert results.successful_upload_count == 0
                assert results.failed_upload_count == 6
                assert len(results.failed) == 6
                assert results.failed == [
                    "16675.txt",
                    "16675.txt.meta.json",
                    "22297.txt",
                    "22297.txt.meta.json",
                    "35887.txt",
                    "35887.txt.meta.json",
                ]

        async def test_upload_texts_http_error(self, upload_session_response: UploadSession) -> None:
            with patch.object(
                aiohttp.ClientSession, "post", side_effect=HTTPError("https://error.com", 503, "test error", "", None)  # type: ignore
            ):
                s3 = S3()

                files = [
                    DeepsetCloudFile(name="one.txt", text="1"),
                    DeepsetCloudFile(name="two.txt", text="2"),
                    DeepsetCloudFile(name="three.txt", text="3"),
                ]

                results = await s3.upload_texts(upload_session_response, files)
                assert results.total_files == 3
                assert results.successful_upload_count == 0
                assert results.failed_upload_count == 3
                assert len(results.failed) == 3
                assert results.failed == [
                    "one.txt",
                    "two.txt",
                    "three.txt",
                ]

        async def test_upload_texts_with_metadata_http_error(self, upload_session_response: UploadSession) -> None:
            with patch.object(
                aiohttp.ClientSession, "post", side_effect=HTTPError("https://error.com", 503, "test error", "", None)  # type: ignore
            ):
                s3 = S3()

                files = [
                    DeepsetCloudFile(name="one.txt", text="1", meta={"something": 1}),
                    DeepsetCloudFile(name="two.txt", text="2", meta={"something": 2}),
                    DeepsetCloudFile(name="three.txt", text="3", meta={"something": 3}),
                ]

                results = await s3.upload_texts(upload_session_response, files)
                assert results.total_files == 6
                assert results.successful_upload_count == 0
                assert results.failed_upload_count == 6
                assert len(results.failed) == 6
                assert results.failed == [
                    "one.txt",
                    "one.txt.meta.json",
                    "two.txt",
                    "two.txt.meta.json",
                    "three.txt",
                    "three.txt.meta.json",
                ]


@pytest.mark.asyncio
class TestValidateFilePaths:
    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/file1.txt"), Path("/home/user/file2.txt")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths(self, file_paths: List[Path]) -> None:
        await S3.validate_file_paths(file_paths)

    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/file2.json")],
            [Path("/home/user/file1.md")],
            [Path("/home/user/file1.docx")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file2.pdf.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths_with_broken_meta_field(self, file_paths: List[Path]) -> None:
        with pytest.raises(ValueError):
            await S3.validate_file_paths(file_paths)
