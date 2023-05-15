"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# connection to deepset Cloud
API_URL: str = os.getenv("API_URL", "https://api.cloud.deepset.ai/")
API_KEY: str = os.getenv("API_KEY", "")

# configuration to use a selectd workspace
DEFAULT_WORKSPACE_NAME: str = os.getenv("DEFAULT_WORKSPACE_NAME", "")


@dataclass
class CommonConfig:
    """Common config for connecting to Deepset Cloud API."""

    api_key: str = API_KEY
    api_url: str = API_URL

    def __post_init__(self) -> None:
        """Validate config."""
        assert (
            self.api_key != ""
        ), "API_KEY environment variable must be set. Please visit https://cloud.deepset.ai/settings/connections to get an API key."
        assert self.api_url != "", "API_URL environment variable must be set"
