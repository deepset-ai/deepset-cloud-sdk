import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import aiohttp
import pytest
from pyrate_limiter import Duration, Rate
from tqdm.asyncio import tqdm

from deepset_cloud_sdk._api.upload_sessions import UploadSession
from deepset_cloud_sdk._s3.upload import S3, RetryableHttpError, make_safe_file_name
from deepset_cloud_sdk.models import DeepsetCloudFile


class TestUploadsS3:
    class TestHelpers:
        @pytest.mark.parametrize(
            "input_file_name,expected_file_name",
            [
                ("hello.txt", "hello.txt"),
                # unprintable characters
                (
                    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
                    "_" * 32,
                ),
                # additional special characters
                ("""#%"'|<>{}`^[]~\\""", "_" * 15),
            ],
        )
        def test_make_safe_file_name(self, input_file_name: str, expected_file_name: str) -> None:
            safe_name = make_safe_file_name(input_file_name)
            assert safe_name == expected_file_name

    @patch.object(aiohttp.ClientSession, "post")
    @pytest.mark.asyncio
    class TestS3:
        @patch.object(tqdm, "gather")
        async def test_upload_in_memory_with_progress(
            self, tqdm_gather: Mock, post: Mock, upload_session_response: UploadSession
        ) -> None:
            async with S3() as s3:
                files = [
                    DeepsetCloudFile("one.txt", "one"),
                    DeepsetCloudFile("two.txt", "two"),
                    DeepsetCloudFile("three.txt", "three"),
                ]
                await s3.upload_in_memory(upload_session=upload_session_response, files=files, show_progress=True)

                assert tqdm_gather.call_count == 1

        async def test_upload_in_memory_with_progress_check_http_calls(
            self, post: Mock, upload_session_response: UploadSession
        ) -> None:
            async with S3() as s3:
                files = [
                    DeepsetCloudFile("one.txt", "one"),
                    DeepsetCloudFile("two.txt", "two"),
                    DeepsetCloudFile("three.txt", "three"),
                ]
                await s3.upload_in_memory(upload_session=upload_session_response, files=files, show_progress=True)

                assert post.call_count == 3

        @patch.object(tqdm, "gather")
        async def test_upload_in_memory_without_progress(
            self, tqdm_gather: Mock, post: Mock, upload_session_response: UploadSession
        ) -> None:
            async with S3() as s3:
                files = [
                    DeepsetCloudFile("one.txt", "one"),
                    DeepsetCloudFile("two.txt", "two"),
                    DeepsetCloudFile("three.txt", "three"),
                ]
                await s3.upload_in_memory(upload_session=upload_session_response, files=files, show_progress=False)

                assert tqdm_gather.call_count == 0

                assert post.call_count == 3

        async def test_upload_files_without_progress(self, post: Mock, upload_session_response: UploadSession) -> None:
            async with S3() as s3:
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

        async def test_upload_rate(self, post: Mock, upload_session_response: UploadSession) -> None:
            rate = Rate(3000, Duration.SECOND)
            async with S3(rate_limit=rate) as s3:
                number_of_files_to_upload = 9000
                files = [DeepsetCloudFile(name=f"{i}.txt", text=f"{i}") for i in range(number_of_files_to_upload)]
                start = time.monotonic()
                await s3.upload_in_memory(upload_session_response, files)
                time_taken = time.monotonic() - start
                expected_time_taken = number_of_files_to_upload / rate.limit
                assert time_taken == pytest.approx(expected_time_taken, 1)

        async def test_upload_files_from_path_http_error(self, upload_session_response: UploadSession) -> None:
            exception = aiohttp.ClientResponseError(request_info=Mock(), history=Mock(), status=503)
            with patch.object(aiohttp.ClientSession, "post", side_effect=exception):
                async with S3() as s3:
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
                    assert [f.file_name for f in results.failed] == [
                        "16675.txt",
                        "16675.txt.meta.json",
                        "22297.txt",
                        "22297.txt.meta.json",
                        "35887.txt",
                        "35887.txt.meta.json",
                    ]
                    assert all(isinstance(f.exception, RetryableHttpError) for f in results.failed)

        async def test_upload_files_from_path_with_client_disconnect_error(
            self, upload_session_response: UploadSession
        ) -> None:
            exception = aiohttp.ServerDisconnectedError()
            with patch.object(aiohttp.ClientSession, "post", side_effect=exception):
                async with S3() as s3:
                    files = [
                        Path("./tests/test_data/msmarco.10/16675.txt"),
                        Path("./tests/test_data/msmarco.10/16675.txt.meta.json"),
                    ]

                    results = await s3.upload_files_from_paths(upload_session_response, files)
                    assert results.total_files == 2
                    assert results.successful_upload_count == 0
                    assert results.failed_upload_count == 2
                    assert len(results.failed) == 2
                    assert [f.file_name for f in results.failed] == ["16675.txt", "16675.txt.meta.json"]
                    assert all(isinstance(f.exception, RetryableHttpError) for f in results.failed)

        async def test_upload_in_memory_http_error(self, upload_session_response: UploadSession) -> None:
            exception = aiohttp.ClientResponseError(request_info=Mock(), history=Mock(), status=503)
            with patch.object(aiohttp.ClientSession, "post", side_effect=exception):
                async with S3() as s3:
                    files = [
                        DeepsetCloudFile(name="one.txt", text="1"),
                        DeepsetCloudFile(name="two.txt", text="2"),
                        DeepsetCloudFile(name="three.txt", text="3"),
                    ]

                    results = await s3.upload_in_memory(upload_session_response, files)
                    assert results.total_files == 3
                    assert results.successful_upload_count == 0
                    assert results.failed_upload_count == 3
                    assert len(results.failed) == 3

                    assert [f.file_name for f in results.failed] == [
                        "one.txt",
                        "two.txt",
                        "three.txt",
                    ]
                    assert all(isinstance(f.exception, RetryableHttpError) for f in results.failed)

        async def test_upload_in_memory_with_metadata_http_error(self, upload_session_response: UploadSession) -> None:
            exception = aiohttp.ClientResponseError(request_info=Mock(), history=Mock(), status=503)
            with patch.object(aiohttp.ClientSession, "post", side_effect=exception):
                async with S3() as s3:
                    files = [
                        DeepsetCloudFile(name="one.txt", text="1", meta={"something": 1}),
                        DeepsetCloudFile(name="two.txt", text="2", meta={"something": 2}),
                        DeepsetCloudFile(name="three.txt", text="3", meta={"something": 3}),
                    ]

                    results = await s3.upload_in_memory(upload_session_response, files)
                    assert results.total_files == 6
                    assert results.successful_upload_count == 0
                    assert results.failed_upload_count == 6
                    assert len(results.failed) == 6
                    assert [f.file_name for f in results.failed] == [
                        "one.txt",
                        "one.txt.meta.json",
                        "two.txt",
                        "two.txt.meta.json",
                        "three.txt",
                        "three.txt.meta.json",
                    ]
                    assert all(isinstance(f.exception, RetryableHttpError) for f in results.failed)

        @pytest.mark.parametrize("status", [503, 502, 500, 504, 408, 400])
        @patch("aiohttp.ClientSession")
        async def test_upload_file_retries_for_exception(
            self, mock_session: Mock, upload_session_response: UploadSession, status: int
        ) -> None:
            exception = aiohttp.ClientResponseError(
                request_info=Mock(), history=Mock(), status=status, message="reason"
            )
            with patch.object(aiohttp.ClientSession, "post") as post_mock:
                post_mock.return_value.__aenter__.return_value.raise_for_status = MagicMock(side_effect=exception)
                post_mock.return_value.__aenter__.return_value.text.return_value = "<xml>error</xml>"
                async with S3() as s3:
                    with pytest.raises(RetryableHttpError, match="reason - <xml>error</xml>"):
                        await s3._upload_file_with_retries("one.txt", upload_session_response, "123", mock_session)

        @pytest.mark.parametrize("status", [422, 501])
        @patch("aiohttp.ClientSession")
        async def test_upload_file_does_not_retry_for_exception(
            self, mock_session: Mock, upload_session_response: UploadSession, status: int
        ) -> None:
            exception = aiohttp.ClientResponseError(
                request_info=Mock(), history=Mock(), status=status, message="reason"
            )
            with patch.object(aiohttp.ClientSession, "post") as post_mock:
                post_mock.return_value.__aenter__.return_value.raise_for_status = MagicMock(side_effect=exception)
                post_mock.return_value.__aenter__.return_value.text.return_value = "<xml>error</xml>"
                async with S3() as s3:
                    with pytest.raises(aiohttp.ClientResponseError, match="reason - <xml>error</xml>"):
                        await s3._upload_file_with_retries("one.txt", upload_session_response, "123", mock_session)

        @pytest.mark.parametrize("status", [422, 501])
        @patch("aiohttp.ClientSession")
        async def test_upload_file_does_not_retry_for_exception_failing_json(
            self, mock_session: Mock, upload_session_response: UploadSession, status: int
        ) -> None:
            exception = aiohttp.ClientResponseError(
                request_info=Mock(), history=Mock(), status=status, message="reason"
            )
            with patch.object(aiohttp.ClientSession, "post") as post_mock:
                post_mock.return_value.__aenter__.return_value.raise_for_status = MagicMock(side_effect=exception)
                post_mock.return_value.__aenter__.return_value.text.side_effect = Exception("error")
                async with S3() as s3:
                    with pytest.raises(aiohttp.ClientResponseError, match="reason"):
                        await s3._upload_file_with_retries("one.txt", upload_session_response, "123", mock_session)

        @patch("aiohttp.ClientSession")
        async def test_upload_file_retries_for_client_connection_exception(
            self,
            mock_session: Mock,
            upload_session_response: UploadSession,
        ) -> None:
            exception = aiohttp.ClientConnectionError()
            with patch.object(aiohttp.ClientSession, "post", side_effect=exception):
                async with S3() as s3:
                    with pytest.raises(RetryableHttpError):
                        await s3._upload_file_with_retries("one.txt", upload_session_response, "123", mock_session)
