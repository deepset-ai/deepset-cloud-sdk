import os
from unittest.mock import Mock

import httpx
import pytest
import structlog
from dotenv import load_dotenv

from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import DeepsetCloudAPI

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
def deepset_cloud_api(unit_config: CommonConfig, mocked_client: Mock) -> DeepsetCloudAPI:
    return DeepsetCloudAPI(config=unit_config, client=mocked_client)
