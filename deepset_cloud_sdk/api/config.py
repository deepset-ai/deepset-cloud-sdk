"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

WORKSPACE = os.getenv("WORKSPACE", "default")
API_URL = os.getenv("api_url", "https://api.cloud.deepset.ai/")


@dataclass
class CommonConfig:
    """Common config for connecting to Deepset Cloud API."""

    api_key: str
    api_url: str = API_URL
