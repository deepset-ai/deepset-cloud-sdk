import pytest
import structlog

logger = structlog.get_logger(__name__)


@pytest.fixture
def example_fixture() -> str:
    return "example"
