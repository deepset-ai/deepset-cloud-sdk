from framework.deepset_cloud_api import DeepsetCloudAPI
from framework.deepset_cloud_api.config import CommonConfig

import asyncio
import structlog
logger = structlog.get_logger()
logger.bind(source=__name__)

class OrganizationMismatchException(BaseException):
    pass


def setup(dataset_path: str, workspace_name:str, api_key, url, concurrency, ignore_ingestion):

    org_config = CommonConfig(
        api_key=api_key, api_url=url
    )

    dc_api = DeepsetCloudAPI(org_config)
    exists = dc_api.workspaces.check_workspace_exists(workspace_name)
    if not exists:
        logger.info("workspace does not exist", workspace_name=workspace_name)
        exit(-1)

    ingestion_status_functions = []
    dcUploader = AsyncUploader(config=org_config, concurrency=concurrency)

    wait_for_ingestion = asyncio.run(
        dcUploader.populate_workspace(
            workspace_name, dataset_path
        )
    )

    if not ignore_ingestion:        
        asyncio.run(wait_for_ingestion())

    else:
        logger.info("Ignoring ingestion status, please validate manually", workspace_name=workspace_name)

