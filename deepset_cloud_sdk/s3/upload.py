import asyncio
import json
import os
import re
from dataclasses import dataclass
from http import HTTPStatus
from io import BufferedReader, BytesIO, TextIOWrapper
from pathlib import Path
from typing import Any, Callable, Coroutine, List, Tuple
from urllib.error import HTTPError
from urllib.parse import quote

import aiohttp
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from deepset_cloud_sdk.api.upload_sessions import (
    AWSPrefixedRequesetConfig,
    UploadSession,
)
from deepset_cloud_sdk.models import DeepsetCloudFile

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
    transformed = re.sub("[\\\\#%\"'\|<>\{\}`\^\[\]~\x00-\x1F]", "_", file_name)
    return quote(transformed)


class S3:
    def __init__(self, concurrency: int = 120):
        self.connector = aiohttp.TCPConnector(limit=concurrency)
        self.semaphore = asyncio.BoundedSemaphore(concurrency)

    @retry(retry=retry_if_exception_type(HTTPError), stop=stop_after_attempt(3), wait=wait_fixed(0.5))  # type: ignore
    async def _upload_file_with_retries(
        self,
        file_name: str,
        upload_session: UploadSession,
        content: Any,
        client_session: aiohttp.ClientSession,
    ) -> aiohttp.ClientResponse:
        aws_safe_name = make_safe_file_name(file_name)
        aws_config = upload_session.aws_prefixed_request_config

        file_data = aiohttp.FormData()
        for key in aws_config.fields:
            file_data.add_field(key, aws_config.fields[key])
        file_data.add_field("file", content, filename=aws_safe_name, content_type="text/plain")
        async with client_session.post(
            aws_config.url,
            data=file_data,
        ) as response:
            response.raise_for_status()

        return response

    async def upload_from_file(
        self,
        file_path: Path,
        upload_session: UploadSession,
        client_session: aiohttp.ClientSession,
    ) -> S3UploadResult:
        async with self.semaphore:
            with open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                try:
                    response = await self._upload_file_with_retries(file_name, upload_session, file, client_session)
                    return S3UploadResult(file_name=file_name, success=True)
                except Exception as ue:
                    logger.warn(
                        "Could not upload a file to S3", file_name=file_name, session_id=upload_session.session_id
                    )
                    return S3UploadResult(file_name=file_name, success=False)

    async def upload_from_string(
        self,
        file_name: str,
        upload_session: UploadSession,
        content: str,
        client_session: aiohttp.ClientSession,
    ) -> S3UploadResult:
        try:
            response = await self._upload_file_with_retries(file_name, upload_session, content, client_session)
            return S3UploadResult(file_name=file_name, success=True)
        except Exception as ue:
            logger.warn("Could not upload a file to S3", file_name=file_name, session_id=upload_session.session_id)
            return S3UploadResult(file_name=file_name, success=False)

    async def _process_results(self, tasks: List[Coroutine[Any, Any, S3UploadResult]]) -> S3UploadSummary:
        results: List[S3UploadResult] = await asyncio.gather(*tasks)
        logger.info("Finished uploading files", results=results)

        failed: List[str] = []
        successfully_uploaded = 0
        for result in results:
            if result.success:
                successfully_uploaded += 1
            else:
                failed.append(result.file_name)

        result_summary = S3UploadSummary(
            successful_upload_count=successfully_uploaded,
            failed_upload_count=len(failed),
            failed=failed,
            total_files=len(tasks),
        )

        return result_summary

    async def upload_files_from_paths(self, upload_session: UploadSession, file_paths: List[Path]) -> S3UploadSummary:
        async with aiohttp.ClientSession(connector=self.connector) as client_session:
            tasks = []

            for file_path in file_paths:
                tasks.append(self.upload_from_file(file_path, upload_session, client_session))

            result_summary = await self._process_results(tasks)
            return result_summary

    async def upload_texts(self, upload_session: UploadSession, dc_files: List[DeepsetCloudFile]) -> S3UploadSummary:
        async with aiohttp.ClientSession(connector=self.connector) as client_session:
            tasks = []

            for file in dc_files:
                # raw data
                file_name = file.name
                tasks.append(self.upload_from_string(file_name, upload_session, file.text, client_session))

                # meta
                meta_name = f"{file_name}.meta.json"
                metadata = json.dumps(file.meta)
                tasks.append(self.upload_from_string(meta_name, upload_session, metadata, client_session))

            result_summary = await self._process_results(tasks)
            return result_summary
