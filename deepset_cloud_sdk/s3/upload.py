import asyncio
from dataclasses import dataclass
from io import BufferedReader, TextIOWrapper
import re
from typing import Callable, List, Tuple
from urllib.error import HTTPError
from deepset_cloud_sdk.api.upload_sessions import AWSPrefixedRequesetConfig
from urllib.parse import quote_plus
import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
import structlog
from deepset_cloud_sdk.api.upload_sessions import UploadSession
from http import HTTPStatus

logger = structlog.get_logger(__name__)


@dataclass
class S3UploadSummary:
    total_files: int
    successful_upload_count: int
    failed_upload_count: int
    failed: List[str]


@dataclass
class S3UploadResult:
    file_name: str
    success: bool


def make_safe_file_name(file_name: str) -> str:
    # characters to avoid: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
    transformed = re.sub('[#%"\|<>\{\}`\^\[\]~ \x00\x08\x0B\x0C\x0E-\x1F]', "_", file_name)
    return quote_plus(transformed)


class S3:
    def __init__(self, concurrency: int = 120):
        self.connector = aiohttp.TCPConnector(limit=concurrency)

    @retry(retry=retry_if_exception_type(HTTPError), stop=stop_after_attempt(3), wait=wait_fixed(0.5))  # type: ignore
    async def _upload_file_with_retries(
        self,
        file_name: str,
        upload_session: UploadSession,
        buffered_reader: BufferedReader,
        client_session: aiohttp.ClientSession,
    ) -> aiohttp.ClientResponse:
        aws_safe_name = make_safe_file_name(file_name)
        aws_config = upload_session.aws_prefixed_request_config

        file_data = aiohttp.FormData()
        for key in aws_config.fields:
            file_data.add_field(key, aws_config.fields[key])
        file_data.add_field("file", buffered_reader, filename=aws_safe_name, content_type="text/plain")
        async with client_session.post(
            aws_config.url,
            data=file_data,
        ) as response:
            response.raise_for_status()

        return response

    async def upload_file(
        self,
        file_name: str,
        upload_session: UploadSession,
        buffered_reader: BufferedReader,
        client_session: aiohttp.ClientSession,
    ) -> S3UploadResult:
        try:
            response = await self._upload_file_with_retries(file_name, upload_session, buffered_reader, client_session)
            return S3UploadResult(file_name=file_name, success=True)
        except Exception as ue:
            logger.warn("Could not upload a file to S3", file_name=file_name, session_id=upload_session.session_id)
            return S3UploadResult(file_name=file_name, success=False)
        finally:
            buffered_reader.close()

    async def upload_files(
        self, upload_session: UploadSession, get_files: List[Callable[[], Tuple[str, BufferedReader]]]
    ) -> S3UploadSummary:
        client_session = aiohttp.ClientSession(connector=self.connector)
        tasks = []

        for get_file in get_files:
            file_name, buffered_reader = get_file()
            tasks.append(self.upload_file(file_name, upload_session, buffered_reader, client_session))

        results: List[S3UploadResult] = await asyncio.gather(*tasks)
        logger.info("Finished uploading files", results=results)
        await client_session.close()

        failed: List[str] = []
        successfully_uploaded = 0
        for result in results:
            if result.success:
                successfully_uploaded += 1
            else:
                failed.append(result.file_path)

        result_summary = S3UploadSummary(
            successful_upload_count=successfully_uploaded,
            failed_upload_count=len(failed),
            failed=failed,
            total_files=len(get_files),
        )

        return result_summary
