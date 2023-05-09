from typing import List
import httpx
from httpx import HTTPError

from httpx import Response
from framework.deepset_cloud_api.config import CommonConfig

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import urllib.parse
from typing import Dict

import structlog

logger = structlog.get_logger()
DEFAULT_WORKSPACE = "default"
logger.bind(source=__name__)


class Files:
    def __init__(self, config: CommonConfig):
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.base_url = (
            lambda workspace_name: f"{config.api_url}/workspaces/{workspace_name}/files"
        )

    def list(
        self, workspace_name: str, limit: int = 100, page_number: int = 1
    ) -> Response:
        x = self.base_url(workspace_name)
        response = httpx.get(
            f"{x}?limit={limit}&page_number={page_number}",
            headers=self.headers,
            timeout=20,
        )
        logger.info(
            f"GET list of files in workspace",
            workspace=workspace_name,
            status=response.status_code,
        )
        if response.status_code == 200:
            logger.info(f"Found {len(response.json()['data'])} files")

        return response

    def upload_from_binary(
        self, workspace_name: str, file: bytearray, filename: str, metadata: Dict = {}
    ) -> Response:
        timeout = httpx.Timeout(20, connect=5)
        response = httpx.post(
            f"{self.base_url(workspace_name)}",
            files={"file": (filename, file, "text/plain")},
            headers=self.headers,
            data={"meta": metadata},
            timeout=timeout,
        )
        response.raise_for_status()
        logger.info(f"POST file to workspace", workspace=workspace_name, filename=filename, status=response.status_code)  # type: ignore
        return response

    def delete_all(self, workspace_name):

        response = httpx.delete(
            f"{self.base_url(workspace_name)}", headers=self.headers
        )
        logger.info(
            f"DELETE all files in workspace",
            workspace=workspace_name,
            status=response.status_code,
        )
        return response

    def delete_file(self, file_id: str, workspace_name: str) -> Response:
        response = httpx.delete(
            f"{self.base_url(workspace_name)}/{file_id}", headers=self.headers
        )
        logger.info(
            f"DELETE file in workspace",
            workspace=workspace_name,
            file=file_id,
            status=response.status_code,
        )
        return response

    @retry(  # type: ignore
        retry=retry_if_exception_type(HTTPError),
        wait=wait_fixed(5),
        stop=stop_after_attempt(3),
    )
    def get_remaining_files(self, workspace_name) -> Response:
        response = self.list(workspace_name)
        response.raise_for_status()
        return response

    @retry(  # type: ignore
        retry=retry_if_exception_type(HTTPError),
        wait=wait_fixed(5),
        stop=stop_after_attempt(3),
    )
    def delete_file_retry(self, workspace_name: str, file_id: str) -> Response:
        response = self.delete_file(file_id, workspace_name)
        response.raise_for_status()
        return response

    def delete_remaining_files(self, workspace_name: str) -> None:
        try:
            remaining_files_response = self.get_remaining_files(  # type: ignore # <nothing> not callable - seems like a false flag from mypy
                workspace_name=workspace_name
            )
            remaining_files = remaining_files_response.json()["data"]

            for file in remaining_files:
                file_id = file["file_id"]
                self.delete_file_retry(workspace_name=workspace_name, file_id=file_id)  # type: ignore # <nothing> not callable - seems like a false flag from mypy
        except Exception:
            logger.warn("Could not delete the files remaining in the workspace")

    def get(self, workspace_name: str, file_name: str) -> Response:
        url_file_name = urllib.parse.quote(file_name)
        response = httpx.get(f"{self.base_url(workspace_name)}/{url_file_name}")
        response.raise_for_status()
        return response

    def check_files_exist(self, workspace_name: str, files: List[str]) -> None:
        file_responses = []
        for file in files:
            try:
                file_response = self.get(workspace_name, file)
                file_responses.append(file_response.json()["name"])
            except:
                logger.warn(
                    f"Could not find file in workspace",
                    workspace=workspace_name,
                    file=file,
                )

        assert len(files) == len(
            file_responses
        ), f"Expected {files}, Found {file_responses}"
