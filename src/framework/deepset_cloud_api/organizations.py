import httpx
from framework.deepset_cloud_api.config import CommonConfig

DEFAULT_WORKSPACE = "default"


class Organizations:
    def __init__(self, config: CommonConfig):
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.base_url = f"{config.api_url}/organization"

    def get(self):
        return httpx.get(self.base_url, headers=self.headers)
