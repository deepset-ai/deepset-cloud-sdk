import asyncio
from io import BufferedReader, TextIOWrapper
import re
from typing import Callable, List, Tuple
from urllib.error import HTTPError
from deepset_cloud_sdk.api.upload_sessions import AWSPrefixedRequesetConfig
import urllib
import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
import structlog
from deepset_cloud_sdk.api.upload_sessions import UploadSession

logger = structlog.get_logger(__name__)


def make_safe_file_name(file_name: str) -> str:
    # characters to avoid: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
    transformed = re.sub('[#%"\|<>\{\}`\^\[\]~ \x00\x08\x0B\x0C\x0E-\x1F]', "_", file_name)
    return urllib.parse.quote_plus(transformed)


class S3:
    def __init__(self, concurrency: int = 120):
        self.connector = aiohttp.TCPConnector(limit=concurrency)

    @retry(retry=retry_if_exception_type(HTTPError), stop=stop_after_attempt(3), wait=wait_fixed(0.5))  # type: ignore
    async def upload_file(
        self,
        file_name: str,
        upload_session: UploadSession,
        buffered_reader: BufferedReader,
        client_session: aiohttp.ClientSession,
    ) -> aiohttp.ClientResponse:
        aws_safe_name = make_safe_file_name(file_name)
        aws_config = upload_session.aws_prefixed_request_config
        try:
            file_data = aiohttp.FormData()
            for key in aws_config.fields:
                file_data.add_field(key, aws_config.fields[key])
            file_data.add_field("file", buffered_reader, filename=aws_safe_name, content_type="text/plain")
            async with client_session.post(
                aws_config.url,
                data=file_data,
            ) as response:
                response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            buffered_reader.close()
        return response

    async def upload_files(
        self, upload_session: UploadSession, get_files: List[Callable[[], Tuple[str, BufferedReader]]]
    ):
        client_session = aiohttp.ClientSession(connector=self.connector)
        tasks = []

        for get_file in get_files:
            file_name, buffered_reader = get_file()
            tasks.append(self.upload_file(file_name, upload_session, buffered_reader, client_session))
        results = await asyncio.gather(*tasks)
        logger.info("Finished uploading files", results=results)
        await client_session.close()
