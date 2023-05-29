import datetime
import os
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
import structlog
from dotenv import load_dotenv

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import (
    AWSPrefixedRequestConfig,
    UploadSession,
    UploadSessionsAPI,
)
from deepset_cloud_sdk.s3.upload import S3

load_dotenv()


logger = structlog.get_logger(__name__)


@pytest.fixture
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
