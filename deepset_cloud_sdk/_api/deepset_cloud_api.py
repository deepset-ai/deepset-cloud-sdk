"""DeepsetCloudAPI class."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional

import httpx
import structlog
from httpx import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from deepset_cloud_sdk._api.config import CommonConfig

logger = structlog.get_logger(__name__)


DEFAULT_MAX_ATTEMPTS = 3
SAFE_MODE_MAX_ATTEMPTS = 10


class WorkspaceNotDefinedError(Exception):
    """The workspace_name is not defined. Set an environment variable or pass the `workspace_name` argument."""


class DeepsetCloudAPI:
    """deepset AI Platform API client.

    This class takes care of all API calls to deepset AI Platform and handles authentication and errors.
    """

    def __init__(self, config: CommonConfig, client: httpx.AsyncClient) -> None:
        """Create a deepset AI Platform API client.

        Add a config for authentication and a HTTPX client for
        sending requests.

        :param config: Config for authentication.
        :param client: HTTPX client for sending requests.
        """
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "X-Client-Source": "deepset-cloud-sdk",
        }
        self.base_url = lambda workspace_name: self._get_base_url(config.api_url)(workspace_name)
        self.client = client
        self.max_attempts = SAFE_MODE_MAX_ATTEMPTS if config.safe_mode else DEFAULT_MAX_ATTEMPTS

    @staticmethod
    def _get_base_url(api_url: str) -> Callable:
        def func(workspace_name: str) -> str:
            """Get the base URL for the API.

            :param workspace_name: Name of the workspace to use.
            :return: Base URL.
            """
            if not workspace_name or workspace_name == "":
                raise WorkspaceNotDefinedError(
                    f"Workspace name is not defined. Got '{workspace_name}'. Enter the name of the workspace in `workspace_name`."
                )

            return f"{api_url}/workspaces/{workspace_name}"

        return func

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[DeepsetCloudAPI, None]:
        """Create a new instance of the API client.

        :param config: CommonConfig object.
        """
        if config.safe_mode:
            safe_mode_limits = httpx.Limits(max_keepalive_connections=1, max_connections=1)
            safe_mode_timeout = httpx.Timeout(None)
            async with httpx.AsyncClient(limits=safe_mode_limits, timeout=safe_mode_timeout) as client:
                yield cls(config, client)
        else:
            async with httpx.AsyncClient() as client:
                yield cls(config, client)

    async def get(
        self, workspace_name: str, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout_s: int = 20
    ) -> Response:
        """Make a GET request to the deepset AI Platform API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """

        @retry(
            retry=retry_if_exception_type(httpx.RequestError),
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_fixed(1),
            reraise=True,
        )
        async def retry_wrapper() -> Response:
            return await self._get(workspace_name, endpoint, params, timeout_s)

        return await retry_wrapper()

    async def _get(
        self, workspace_name: str, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout_s: int = 20
    ) -> Response:
        response = await self.client.get(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset AI Platform API.",
            method="GET",
            workspace=workspace_name,
            endpoint=endpoint,
            params=params,
            status=response.status_code,
        )
        return response

    async def post(
        self,
        workspace_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout_s: int = 20,
    ) -> Response:
        """Make a POST request to the deepset AI Platform API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param json: JSON data to pass.
        :param data: Data to pass.
        :param files: Files to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.post(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            json=json,
            data=data,
            files=files,
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset AI Platform API",
            method="POST",
            workspace=workspace_name,
            endpoint=endpoint,
            data=data or {},
            files=files,
            status=response.status_code,
        )
        return response

    async def delete(
        self, workspace_name: str, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout_s: int = 20
    ) -> Response:
        """
        Make a DELETE request to the deepset AI Platform API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.delete(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset AI Platform API",
            method="DELETE",
            workspace=workspace_name,
            endpoint=endpoint,
            params=params,
            status=response.status_code,
        )
        return response

    async def put(
        self,
        workspace_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout_s: int = 20,
    ) -> Response:
        """Make a PUT request to the deepset AI Platform API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param data: Data to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """

        @retry(
            retry=retry_if_exception_type(httpx.ConnectError),
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_fixed(1),
            reraise=True,
        )
        async def retry_wrapper() -> Response:
            return await self._put(workspace_name, endpoint, params, data, timeout_s)

        return await retry_wrapper()

    async def _put(
        self,
        workspace_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout_s: int = 20,
    ) -> Response:
        response = await self.client.put(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            json=data or {},
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset AI Platform API",
            method="PUT",
            workspace=workspace_name,
            endpoint=endpoint,
            data=data or {},
            status=response.status_code,
        )
        return response

    async def patch(
        self,
        workspace_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout_s: int = 20,
    ) -> Response:
        """Make a PATCH request to the deepset AI Platform API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param json: JSON data to pass.
        :param data: Data to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.patch(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            json=json,
            data=data,
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset AI Platform API",
            method="PATCH",
            workspace=workspace_name,
            endpoint=endpoint,
            json=json or {},
            data=data or {},
            status=response.status_code,
        )
        return response


def get_deepset_cloud_api(config: CommonConfig, client: httpx.AsyncClient) -> DeepsetCloudAPI:  # noqa
    """deepset AI Platform API factory. Return an instance of DeepsetCloudAPI.

    :param config: CommonConfig object.
    :param client: httpx.AsyncClient object.
    :return: DeepsetCloudAPI object.
    """
    return DeepsetCloudAPI(config=config, client=client)
