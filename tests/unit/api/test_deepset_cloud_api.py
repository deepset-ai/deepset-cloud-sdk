from unittest.mock import Mock

import httpx
import pytest
from httpx import codes

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import (
    DeepsetCloudAPI,
    get_deepset_cloud_api,
)


@pytest.mark.asyncio
class TestUtilitiesForDeepsetCloudAPI:
    async def test_get_deepset_cloud_api(self, unit_config: CommonConfig) -> None:
        async with httpx.AsyncClient() as client:
            deepset_cloud_api = get_deepset_cloud_api(unit_config, client=client)
            assert (
                deepset_cloud_api.base_url("test_workspace") == "https://fake.dc.api/api/v1/workspaces/test_workspace"
            )
            assert deepset_cloud_api.headers == {
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
            }


@pytest.mark.asyncio
class TestCRUDForDeepsetCloudAPI:
    async def test_get(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.get.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.get("default", "endpoint", params={"param_key": "param_value"}, timeout=123)
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.get.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
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
            timeout=123,
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
            },
            timeout=123,
        )

    async def test_delete(
        self, deepset_cloud_api: DeepsetCloudAPI, unit_config: CommonConfig, mocked_client: Mock
    ) -> None:
        mocked_client.delete.return_value = httpx.Response(status_code=codes.OK, json={"test": "test"})

        result = await deepset_cloud_api.delete("default", "endpoint", params={"param_key": "param_value"}, timeout=123)
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.delete.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
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
            timeout=123,
        )
        assert result.status_code == codes.OK
        assert result.json() == {"test": "test"}
        mocked_client.put.assert_called_once_with(
            "https://fake.dc.api/api/v1/workspaces/default/endpoint",
            params={"param_key": "param_value"},
            data={"data_key": "data_value"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {unit_config.api_key}",
            },
            timeout=123,
        )
