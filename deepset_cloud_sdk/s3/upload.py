import asyncio
import re
from typing import List
from urllib.error import HTTPError
from deepset_cloud_sdk.api.upload_sessions import AWSPrefixedRequesetConfig
import urllib
import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
import structlog

logger = structlog.get_logger(__name__)


def make_safe_file_name(file_name: str) -> str:
    # characters to avoid: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
    transformed = re.sub('[#%"\|<>\{\}`\^\[\]~ \x00\x08\x0B\x0C\x0E-\x1F]', "_", file_name)
    return urllib.parse.quote_plus(transformed)


class S3:
    def __init__(self, concurrency: int = 120):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client_session = aiohttp.ClientSession()

    @retry(retry=retry_if_exception_type(HTTPError), stop=stop_after_attempt(3), wait=wait_fixed(0.5))  # type: ignore
    async def upload_file(
        self,
        file_name: str,
        aws_prefixed_request_config: AWSPrefixedRequesetConfig,
        content: str,
    ) -> aiohttp.ClientResponse:
        aws_safe_name = make_safe_file_name(file_name)

        try:
            async with self.client_session.post(
                aws_prefixed_request_config.url,
                data=aws_prefixed_request_config.fields,
                files={"file": (aws_safe_name, content)},
            ) as response:
                response.raise_for_status()
                logger.info(response.content)
        except Exception as e:
            raise e

        return response

    async def upload_files(
        self,
        file_names: List[str],
        aws_prefixed_request_config: AWSPrefixedRequesetConfig,
        contents: List[str],
    ):
        tasks = []
        for file_name, content in zip(file_names, contents):
            async with self.semaphore:
                tasks.append(self.upload_file(file_name, aws_prefixed_request_config, content))
        results = await asyncio.gather(*tasks)
        logger.info("Finished uploading files", results=results)
