import os
from dataclasses import dataclass

WORKSPACE = os.getenv("WORKSPACE", "default")
API_URL = os.getenv("api_url", "https://api.cloud.deepset.ai/")


@dataclass
class CommonConfig:
    api_key: str
    api_url: str = API_URL
