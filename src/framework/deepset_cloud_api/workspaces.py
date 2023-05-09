import httpx
import structlog
from framework.deepset_cloud_api.config import CommonConfig

logger = structlog.get_logger()
logger.bind(source=__name__)

DEFAULT_WORKSPACE = "default"


class WorkspaceDoesNotExistError(Exception):
    pass


class Workspaces:
    def __init__(self, config: CommonConfig):
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.base_url = f"{config.api_url}/workspaces"

    # list all workspaces
    def list(self):
        response = httpx.get(self.base_url, headers=self.headers)
        logger.info("GET all workspaces in organisation")
        return response

    def create(self, workspace_name):
        data = {"name": workspace_name}
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = httpx.post(self.base_url, json=data, headers=self.headers)
        logger.info(
            "POST Creating a workspace",
            workspace=workspace_name,
            status=response.status_code,
        )
        return response

    def check_workspace_exists(self, workspace_name):
        workspace_response = self.list()
        workspaces = list(map(lambda x: x["name"], workspace_response.json()))
        if workspace_name not in workspaces:
            return False
        return True
