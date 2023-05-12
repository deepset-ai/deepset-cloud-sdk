"""DeepsetCloudAPI class."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional

import httpx
import structlog
from httpx import Response

from deepset_cloud_sdk.api.config import CommonConfig

logger = structlog.get_logger(__name__)


class WorkspaceNotDefinedError(Exception):
    """Workspace not defined error. This exception is raised if a workspace_name is not defined.

    This can happen if neither an environment variable was set, nor a workspace_name was passed as an argument.
    """


class DeepsetCloudAPI:
    """Deepset cloud API client.

    This class takes care of all API calls to deepset Cloud and handles authentication and error handling.
    """

    def __init__(self, config: CommonConfig, client: httpx.AsyncClient) -> None:
        """Create a deepset cloud api client.

        Add a config for authencation and a httpx client for
        sending requests.

        :param config: Config for authentication.
        :param client: HTTPX client for sending requests.
        """
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.base_url = lambda workspace_name: self._get_base_url(config.api_url)(workspace_name)
        self.client = client

    @staticmethod
    def _get_base_url(api_url: str) -> Callable:
        def func(workspace_name: str) -> str:
            """Get the base url for the API.

            :param workspace_name: Name of the workspace to use.
            :return: Base url.
            """
            if not workspace_name or workspace_name == "":
                raise WorkspaceNotDefinedError(f"Workspace name not defined. Got '{workspace_name}'")

            return f"{api_url}/workspaces/{workspace_name}"

        return func

    @classmethod
    @asynccontextmanager
    async def factory(cls, config: CommonConfig) -> AsyncGenerator[DeepsetCloudAPI, None]:
        """Create a new instance of the API client.

        :param config: CommonConfig object.
        """
        async with httpx.AsyncClient() as client:
            yield cls(config, client)

    async def get(
        self, workspace_name: str, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout_s: int = 20
    ) -> Response:
        """Make a GET request to the deepset Cloud API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.get(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset Cloud API",
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
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout_s: int = 20,
    ) -> Response:
        """Make a POST request to the deepset Cloud API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param data: Data to pass.
        :param files: Files to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.post(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            json=data or {},
            files=files,
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset Cloud API",
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
        Make a DELETE request to the deepset Cloud API.

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
            "Called deepset Cloud API",
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
        """Make a PUT request to the deepset Cloud API.

        :param workspace_name: Name of the workspace to use.
        :param endpoint: Endpoint to call.
        :param params: Query parameters to pass.
        :param data: Data to pass.
        :param timeout_s: Timeout in seconds.
        :return: Response object.
        """
        response = await self.client.put(
            f"{self.base_url(workspace_name)}/{endpoint}",
            params=params or {},
            json=data or {},
            headers=self.headers,
            timeout=timeout_s,
        )
        logger.debug(
            "Called deepset Cloud API",
            method="PUT",
            workspace=workspace_name,
            endpoint=endpoint,
            data=data or {},
            status=response.status_code,
        )
        return response


def get_deepset_cloud_api(config: CommonConfig, client: httpx.AsyncClient) -> DeepsetCloudAPI:
    """Deepset Cloud API factory. Returns an instance of DeepsetCloudAPI.

    :param config: CommonConfig object.
    :param client: httpx.AsyncClient object.
    :return: DeepsetCloudAPI object.
    """
    return DeepsetCloudAPI(config=config, client=client)
