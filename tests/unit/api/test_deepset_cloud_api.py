from unittest.mock import Mock

import httpx
import pytest
from httpx import codes

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import (
    DeepsetCloudAPI,
    WorkspaceNotDefinedError,
)


@pytest.mark.asyncio
class TestUtilitiesForDeepsetCloudAPI:
    async def test_deepset_cloud_api_factory(self, unit_config: CommonConfig) -> None:
        async with DeepsetCloudAPI.factory(unit_config) as deepset_cloud_api:
            assert (
                deepset_cloud_api.base_url("test_workspace") == "https://fake.dc.api/api/v1/workspaces/test_workspace"
            )
            assert deepset_cloud_api.headers == {
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            }

    async def test_deepset_cloud_api_raises_exception_if_no_workspace_is_defined(
        self, deepset_cloud_api: DeepsetCloudAPI
    ) -> None:
        with pytest.raises(WorkspaceNotDefinedError):
            await deepset_cloud_api.get("", "endpoint")


@pytest.mark.asyncio
class TestCommonConfig:
    async def test_common_config_raises_exception_if_no_api_key_is_defined(self) -> None:
        with pytest.raises(AssertionError):
            CommonConfig(api_key="", api_url="https://fake.dc.api")

    async def test_common_config_raises_exception_if_no_api_url_is_defined(self) -> None:
        with pytest.raises(AssertionError):
            CommonConfig(api_key="your-key", api_url="")

    async def test_common_config_removes_last_backslash(self) -> None:
        assert CommonConfig(api_key="your-key", api_url="https://fake.dc.api/").api_url == "https://fake.dc.api"


@pytest.mark.asyncio
class TestCRUDForDeepsetCloudAPI:
    async def test_get(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.get.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.get("default", "endpoint", params={"param_key": "param_value"}, timeout_s=123)
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.get.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            },
            timeout=123,
        )

    async def test_get_retry(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.get.side_effect = [
            httpx.ReadTimeout(message="read timeout"),
            httpx.RequestError(message="read error"),
            httpx.Response(status_code=codes.OK, json={"test": "test"}),
        ]

        result = await deepset_cloud_api.get("default", "endpoint", params={"param_key": "param_value"}, timeout_s=123)
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        assert mocked_client.get.call_count == 3

        mocked_client.get.assert_called_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            },
            timeout=123,
        )

    async def test_post(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.post.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.post(
            "default",
            "endpoint",
            params={"param_key": "param_value"},
            data={"data_key": "data_value"},
            files={"file": ("my_file", "fake-file-binary", "text/csv")},
            timeout_s=123,
        )
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.post.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            json={"data_key": "data_value"},
            files={"file": ("my_file", "fake-file-binary", "text/csv")},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            },
            timeout=123,
        )

    async def test_delete(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.delete.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.delete(
            "default", "endpoint", params={"param_key": "param_value"}, timeout_s=123
        )
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.delete.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            },
            timeout=123,
        )

    async def test_put(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.put.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.put(
            "default",
            "endpoint",
            params={"param_key": "param_value"},
            data={"data_key": "data_value"},
            timeout_s=123,
        )
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.put.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            json={"data_key": "data_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
                "X-Client-Source": "deepset-cloud-sdk",
            },
            timeout=123,
        )
