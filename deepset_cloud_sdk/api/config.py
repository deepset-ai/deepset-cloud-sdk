"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# connection to deepset Cloud
API_URL = os.getenv("API_URL", "https://api.cloud.deepset.ai/")
API_KEY = os.getenv("API_KEY", "")

# configuration to use a selectd workspace
DEFAULT_WORKSPACE_NAME = os.getenv("DEFAULT_WORKSPACE_NAME", "default")


@dataclass
class CommonConfig:
    """Common config for connecting to Deepset Cloud API."""

    api_key: str = API_KEY
    api_url: str = API_URL

    def __post_init__(self) -> None:
        """Validate config."""
        assert self.api_key != "", "API_KEY environment variable must be set"
        assert self.api_url != "", "API_URL environment variable must be set"
