"""Module for upload-related S3 operations."""
import asyncio
import json
import os
import re
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Coroutine, List, Optional
from urllib.parse import quote

import aiofiles
import aiohttp
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from tqdm.asyncio import tqdm

from deepset_cloud_sdk._api.upload_sessions import (
    AWSPrefixedRequestConfig,
    UploadSession,
)
from deepset_cloud_sdk.models import DeepsetCloudFile

logger = structlog.get_logger(__name__)


class RetryableHttpError(Exception):
    """An error that indicates a function should be retried."""

    def __init__(self, error: aiohttp.ClientResponseError) -> None:
        """Store the original exception."""
        self.error = error


@dataclass
class S3UploadResult:
    """Stores the result of an upload to S3."""

    file_name: str
    success: bool
    exception: Optional[Exception] = None


@dataclass
class S3UploadSummary:
    """A summary of the S3 upload results."""

    total_files: int
    successful_upload_count: int
    failed_upload_count: int
    failed: List[S3UploadResult]


def make_safe_file_name(file_name: str) -> str:
    """
    Transform a given string to a representation that S3 accepts.

    :param str: The file name.
    :return str: The transformed string.
    For character exclusions, see
    [Creating object key names](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html).
    """
    transformed = re.sub(r"[\\\\#%\"'\|<>\{\}`\^\[\]~\x00-\x1F]", "_", file_name)
    return quote(transformed)


class S3:
    """Client for S3 operations related to deepset Cloud uploads."""

    def __init__(self, concurrency: int = 120):
        """
        Initialize the client.

        :param concurrency: The number of concurrent upload requests
        """
        self.connector = aiohttp.TCPConnector(limit=concurrency)
        self.semaphore = asyncio.BoundedSemaphore(concurrency)

    @retry(
        retry=retry_if_exception_type(RetryableHttpError),
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.5),
        reraise=True,
    )
    async def _upload_file_with_retries(
        self,
        file_name: str,
        upload_session: UploadSession,
        content: Any,
        client_session: aiohttp.ClientSession,
    ) -> aiohttp.ClientResponse:
        """Upload a file to the prefixed S3 namespace.

        :param file_path: The path to upload from.
        :param upload_session: UploadSession to associate the upload with.
        :param client_session: The aiohttp ClientSession to use for this request.
        :param headers: The headers for the request
        :return: ClientResponse object.
        """
        aws_safe_name = make_safe_file_name(file_name)
        aws_config = upload_session.aws_prefixed_request_config

        file_data = self._build_file_data(content, aws_safe_name, aws_config)
        try:
            async with client_session.post(
                aws_config.url,
                data=file_data,
                allow_redirects=False,
            ) as response:
                response.raise_for_status()

                if response.status == HTTPStatus.TEMPORARY_REDIRECT:
                    # Sometimes we get a redirect to a different URL from S3 (e.g. the region was added to the URL).
                    # We need to rebuild the file data as FormData does not support multiple requests,
                    # for example during automatic redirects. See https://github.com/aio-libs/aiohttp/issues/5577
                    redirect_url = response.headers["Location"]
                    file_data = self._build_file_data(content, aws_safe_name, aws_config)
                    async with client_session.post(
                        redirect_url,
                        data=file_data,
                        allow_redirects=False,
                    ) as response:
                        response.raise_for_status()
                        return response

                return response
        except aiohttp.ClientResponseError as cre:
            if cre.status in [
                HTTPStatus.INTERNAL_SERVER_ERROR,
                HTTPStatus.BAD_GATEWAY,
                HTTPStatus.SERVICE_UNAVAILABLE,
                HTTPStatus.GATEWAY_TIMEOUT,
                HTTPStatus.REQUEST_TIMEOUT,
            ]:
                raise RetryableHttpError(cre) from cre
            raise

    def _build_file_data(
        self, content: Any, aws_safe_name: str, aws_config: AWSPrefixedRequestConfig
    ) -> aiohttp.FormData:
        file_data = aiohttp.FormData()
        for key in aws_config.fields:
            file_data.add_field(key, aws_config.fields[key])
        file_data.add_field("file", content, filename=aws_safe_name, content_type="text/plain")
        return file_data

    async def upload_from_file(
        self,
        file_path: Path,
        upload_session: UploadSession,
        client_session: aiohttp.ClientSession,
    ) -> S3UploadResult:
        """Upload a file to the prefixed S3 namespace given a path.

        :param file_path: The path to upload from.
        :param upload_session: UploadSession to associate the upload with.
        :param client_session: The aiohttp ClientSession to use for this request.
        :return: S3UploadResult object.
        """
        async with self.semaphore:
            async with aiofiles.open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                content = await file.read()
                try:
                    await self._upload_file_with_retries(file_name, upload_session, content, client_session)
                    return S3UploadResult(file_name=file_name, success=True)
                except Exception as exception:  # pylint: disable=broad-exception-caught
                    logger.error(
                        "Could not upload a file to deepset Cloud",
                        file_name=file_name,
                        session_id=upload_session.session_id,
                        exception=str(exception),
                    )
                    return S3UploadResult(file_name=file_name, success=False, exception=exception)

    async def upload_from_string(
        self,
        file_name: str,
        upload_session: UploadSession,
        content: str,
        client_session: aiohttp.ClientSession,
    ) -> S3UploadResult:
        """Upload text to the prefixed S3 namespace.

        :param file_name: Name of the file.
        :param upload_session: UploadSession to associate the upload with.
        :param client_session: The aiohttp ClientSession to use for this request.
        :param progress: A progress bar.
        :return: S3UploadResult object.
        """
        try:
            await self._upload_file_with_retries(file_name, upload_session, content, client_session)
            return S3UploadResult(file_name=file_name, success=True)
        except Exception as exception:  # pylint: disable=bare-except, disable=broad-exception-caught
            logger.warn(
                "Could not upload a file to deepset Cloud",
                file_name=file_name,
                session_id=upload_session.session_id,
                exception=str(exception),
            )
            return S3UploadResult(file_name=file_name, success=False, exception=exception)

    async def _process_results(
        self, tasks: List[Coroutine[Any, Any, S3UploadResult]], show_progress: bool = True
    ) -> S3UploadSummary:
        """Summarize the results of the uploads to S3.

        :param tasks: List of upload tasks.
        :return: S3UploadResult object.
        """
        results: List[S3UploadResult] = []

        if show_progress:
            results = await tqdm.gather(*tasks, desc="Upload to S3")
        else:
            results = await asyncio.gather(*tasks)

        logger.info(
            "Finished uploading files.",
            number_of_successful_files=len(results),
            failed_files=[r for r in results if not r.success],
        )

        failed: List[S3UploadResult] = []
        successfully_uploaded = 0
        for result in results:
            if result.success:
                successfully_uploaded += 1
            else:
                failed.append(result)

        result_summary = S3UploadSummary(
            successful_upload_count=successfully_uploaded,
            failed_upload_count=len(failed),
            failed=failed,
            total_files=len(tasks),
        )
        if result_summary.successful_upload_count == 0:
            logger.error("Could not upload any files to S3.")

        return result_summary

    async def upload_files_from_paths(
        self, upload_session: UploadSession, file_paths: List[Path], show_progress: bool = True
    ) -> S3UploadSummary:
        """Upload a set of files to the prefixed S3 namespace given a list of paths.

        :param upload_session: UploadSession to associate the upload with.
        :param file_paths: A list of paths to upload.
        :return: S3UploadSummary object.
        """
        async with aiohttp.ClientSession(connector=self.connector) as client_session:
            tasks = []

            for file_path in file_paths:
                tasks.append(self.upload_from_file(file_path, upload_session, client_session))

            result_summary = await self._process_results(tasks, show_progress=show_progress)
            return result_summary

    async def upload_texts(
        self, upload_session: UploadSession, files: List[DeepsetCloudFile], show_progress: bool = True
    ) -> S3UploadSummary:
        """Upload a set of texts to the prefixed S3 namespace given a list of paths.

        :param upload_session: UploadSession to associate the upload with.
        :param files: A list of DeepsetCloudFiles to upload.
        :return: S3UploadSummary object.
        """
        async with aiohttp.ClientSession(connector=self.connector) as client_session:
            tasks = []

            for file in files:
                # raw data
                file_name = file.name
                tasks.append(self.upload_from_string(file_name, upload_session, file.text, client_session))

                # meta
                if file.meta is not None:
                    meta_name = f"{file_name}.meta.json"
                    metadata = json.dumps(file.meta)
                    tasks.append(self.upload_from_string(meta_name, upload_session, metadata, client_session))

            result_summary = await self._process_results(tasks, show_progress=show_progress)

            return result_summary
