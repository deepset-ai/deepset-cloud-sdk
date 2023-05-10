"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

WORKSPACE = os.getenv("WORKSPACE", "default")
API_URL = os.getenv("API_URL", "https://api.cloud.deepset.ai/")
API_KEY = os.getenv("API_KEY", "")


@dataclass
class CommonConfig:
    """Common config for connecting to Deepset Cloud API."""

    api_key: str = API_KEY
    api_url: str = API_URL
