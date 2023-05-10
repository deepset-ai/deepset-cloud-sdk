import os

import pytest
import structlog

from deepset_cloud_sdk.api.config import CommonConfig

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
