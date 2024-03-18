import datetime
import json
import os
from http import HTTPStatus
from typing import Generator, List
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
import structlog
from dotenv import load_dotenv
from faker import Faker
from tenacity import retry, stop_after_delay, wait_fixed

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._api.files import FilesAPI
from deepset_cloud_sdk._api.upload_sessions import (
    AWSPrefixedRequestConfig,
    UploadSession,
    UploadSessionsAPI,
)
from deepset_cloud_sdk._s3.upload import S3

load_dotenv()

logger = structlog.get_logger(__name__)


def _get_file_names(integration_config: CommonConfig, workspace_name: str) -> List[str]:
    list_response = httpx.get(
        f"{integration_config.api_url}/workspaces/{workspace_name}/files",
        headers={"Authorization": f"Bearer {integration_config.api_key}"},
        params={"limit": 100},
    )
    assert list_response.status_code == HTTPStatus.OK
    file_names: List[str] = list_response.json()["data"]
    logger.info("Found files", file_names=file_names)
    return file_names


@pytest.fixture(scope="session")
def integration_config() -> CommonConfig:
    config = CommonConfig(
        api_key=os.getenv("API_KEY", ""),
        api_url=os.getenv("API_URL", ""),
    )
    assert config.api_key != "", "API_KEY environment variable must be set"
    assert config.api_url != "", "API_URL environment variable must be set"
    return config


@pytest.fixture
def unit_config() -> CommonConfig:
    return CommonConfig(api_key="test_api_key", api_url="https://fake.dc.api/api/v1")


@pytest.fixture
def mocked_client() -> Mock:
    return Mock(spec=httpx.AsyncClient)


@pytest.fixture
def mocked_deepset_cloud_api() -> Mock:
    return Mock(spec=DeepsetCloudAPI)


@pytest.fixture
def mocked_upload_sessions_api() -> Mock:
    return Mock(spec=UploadSessionsAPI)


@pytest.fixture
def mocked_files_api() -> Mock:
    return Mock(spec=FilesAPI)


@pytest.fixture
def mocked_s3() -> Mock:
    # TODO: add aws client mock that sends files to aws
    return AsyncMock(spec=S3)


@pytest.fixture
def deepset_cloud_api(unit_config: CommonConfig, mocked_client: Mock) -> DeepsetCloudAPI:
    return DeepsetCloudAPI(config=unit_config, client=mocked_client)


@pytest.fixture
def upload_session_response() -> UploadSession:
    return UploadSession(
        session_id=uuid4(),
        documentation_url="Documentation URL",
        expires_at=datetime.datetime.now(),
        aws_prefixed_request_config=AWSPrefixedRequestConfig(url="uploadURL", fields={"key": "value"}),
    )


@retry(
    stop=stop_after_delay(120),
    wait=wait_fixed(1),
    reraise=True,
)
def _wait_for_file_to_be_available(
    integration_config: CommonConfig, workspace_name: str, expected_file_count: int = 15
) -> None:
    assert len(_get_file_names(integration_config, workspace_name)) >= expected_file_count


@pytest.fixture(scope="session")
def workspace_name(integration_config: CommonConfig) -> Generator[str, None, None]:
    """Create a workspace for the tests and delete it afterwards."""
    fake = Faker()
    workspace_name = f"sdktest_{'_'.join(fake.words(3))}"

    logger.info("Creating workspace", workspace_name=workspace_name)

    # try creating workspace
    response = httpx.post(
        f"{integration_config.api_url}/workspaces",
        json={"name": workspace_name},
        headers={"Authorization": f"Bearer {integration_config.api_key}"},
    )
    assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.CONFLICT)

    try:
        if len(_get_file_names(integration_config=integration_config, workspace_name=workspace_name)) == 0:
            for i in range(15):
                response = httpx.post(
                    f"{integration_config.api_url}/workspaces/{workspace_name}/files",
                    data={"text": "This is text"},
                    files={
                        "meta": (None, json.dumps({"find": "me"}).encode("utf-8")),
                    },
                    params={"file_name": f"example{i}.txt"},
                    headers={"Authorization": f"Bearer {integration_config.api_key}"},
                )
                assert response.status_code == HTTPStatus.CREATED

            _wait_for_file_to_be_available(integration_config, workspace_name, expected_file_count=15)

        yield workspace_name

    finally:
        response = httpx.delete(
            f"{integration_config.api_url}/workspaces/{workspace_name}",
            headers={"Authorization": f"Bearer {integration_config.api_key}"},
        )

        assert response.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)
