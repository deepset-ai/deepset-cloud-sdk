"""Module for upload-related S3 operations."""
import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Coroutine, List
from urllib.error import HTTPError
from urllib.parse import quote

import aiohttp
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from deepset_cloud_sdk.api.upload_sessions import UploadSession
from deepset_cloud_sdk.models import DeepsetCloudFile
from deepset_cloud_sdk.utils.progress_bar import ProgressBar

logger = structlog.get_logger(__name__)


@dataclass
class S3UploadSummary:
    """A summary of the S3 upload results."""

    total_files: int
    successful_upload_count: int
    failed_upload_count: int
    failed: List[str]


@dataclass
class S3UploadResult:
    """Stores the result of an upload to S3."""

    file_name: str
    success: bool


def make_safe_file_name(file_name: str) -> str:
    """
    Transform a given string to a representation that S3 accepts.

    :param str: The file name.
    :return str: The transformed string.
    For character exclusions, see [Creating object key names](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html).
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

    @staticmethod
    async def validate_file_paths(file_paths: List[Path]) -> None:
        """Validate a list of file paths.

        This method validates the file paths and raises a ValueError if the file paths are invalid.
        It also validates if there are meta files mapped to not existing raw files.

        :param file_paths: A list of paths to upload.
        :raises ValueError: If the file paths are invalid.
        """
        allowed_suffixes = {".txt", ".json", ".pdf"}
        for file_path in file_paths:
            if not file_path.suffix.lower() in allowed_suffixes:
                raise ValueError(f"Invalid file extension: {file_path.suffix}")
            if file_path.suffix.lower() == ".json" and not str(file_path).endswith(".meta.json"):
                raise ValueError(
                    f"JSON files are only supported for meta files. Please make sure to name your files '<file_name>.meta.json'. Got {file_path.name}."
                )
        meta_files = [file_path for file_path in file_paths if file_path.suffix.lower() == ".json"]

        not_mapped_meta_files = [
            meta_file_path
            for meta_file_path in meta_files
            if not Path(str(meta_file_path).split(".meta.json")[0]) in file_paths
        ]
        if len(not_mapped_meta_files) > 0:
            raise ValueError(
                f"Meta files without corresponding text files found: {not_mapped_meta_files}. "
                "Please make sure that for each meta file there is a corresponding text file."
                "The mapping needs to be done via file name '<file_name>' and '<file_name>.meta.json'. "
                "For example: 'file1.txt' and 'file1.txt.meta.json'."
            )

    @retry(retry=retry_if_exception_type(HTTPError), stop=stop_after_attempt(3), wait=wait_fixed(0.5))  # type: ignore
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
        :return: ClientResponse object.
        """
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
        progress: ProgressBar,
    ) -> S3UploadResult:
        """Upload a file to the prefixed S3 namespace given a path.

        :param file_path: The path to upload from.
        :param upload_session: UploadSession to associate the upload with.
        :param client_session: The aiohttp ClientSession to use for this request.
        :param progress: A progress bar.
        :return: S3UploadResult object.
        """
        async with self.semaphore:
            with open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                try:
                    await self._upload_file_with_retries(file_name, upload_session, file, client_session)
                    progress.next()
                    return S3UploadResult(file_name=file_name, success=True)
                except HTTPError:
                    logger.warn(
                        "Could not upload a file to S3", file_name=file_name, session_id=upload_session.session_id
                    )
                    progress.next()
                    return S3UploadResult(file_name=file_name, success=False)

    async def upload_from_string(
        self,
        file_name: str,
        upload_session: UploadSession,
        content: str,
        client_session: aiohttp.ClientSession,
        progress: ProgressBar,
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
            progress.next()
            return S3UploadResult(file_name=file_name, success=True)
        except HTTPError:
            logger.warn("Could not upload a file to S3", file_name=file_name, session_id=upload_session.session_id)
            progress.next()
            return S3UploadResult(file_name=file_name, success=False)

    async def _process_results(self, tasks: List[Coroutine[Any, Any, S3UploadResult]]) -> S3UploadSummary:
        """Summarize the results of the uploads to S3.

        :param tasks: List of upload tasks.
        :return: S3UploadResult object.
        """
        results: List[S3UploadResult] = await asyncio.gather(*tasks)
        logger.info(
            "Finished uploading files",
            number_of_successful_files=len(results),
            failed_files=[r for r in results if not r.success],
        )

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
        """Upload a set of files to the prefixed S3 namespace given a list of paths.

        :param upload_session: UploadSession to associate the upload with.
        :param file_paths: A list of paths to upload.
        :return: S3UploadSummary object.
        """
        # validate file paths
        await self.validate_file_paths(file_paths)

        # upload files
        with ProgressBar(
            f"Uploading to S3",
            max=len(file_paths),
        ) as bar:
            async with aiohttp.ClientSession(connector=self.connector) as client_session:
                tasks = []

                for file_path in file_paths:
                    tasks.append(self.upload_from_file(file_path, upload_session, client_session, bar))

                result_summary = await self._process_results(tasks)
                bar.finish()
                return result_summary

    async def upload_texts(self, upload_session: UploadSession, dc_files: List[DeepsetCloudFile]) -> S3UploadSummary:
        """Upload a set of texts to the prefixed S3 namespace given a list of paths.

        :param upload_session: UploadSession to associate the upload with.
        :param dc_files: A list of DeepsetCloudFiles to upload.
        :return: S3UploadSummary object.
        """
        async with aiohttp.ClientSession(connector=self.connector) as client_session:
            tasks = []
            with ProgressBar(
                f"Uploading to S3",
                max=len(dc_files),
            ) as bar:
                for file in dc_files:
                    # raw data
                    file_name = file.name
                    tasks.append(self.upload_from_string(file_name, upload_session, file.text, client_session, bar))

                    # meta
                    meta_name = f"{file_name}.meta.json"
                    metadata = json.dumps(file.meta)
                    tasks.append(self.upload_from_string(meta_name, upload_session, metadata, client_session, bar))

                result_summary = await self._process_results(tasks)
                bar.finish()
                return result_summary
