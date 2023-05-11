import httpx
from deepset_cloud_sdk.api.config import CommonConfig
from deepset_cloud_sdk.api.deepset_cloud_api import get_deepset_cloud_api
from deepset_cloud_sdk.api.files import FilesAPI
from deepset_cloud_sdk.api.upload_sessions import UploadSessionsAPI
from deepset_cloud_sdk.service.files_service import FilesService

config = CommonConfig(
    api_key="adsf",
    api_url="https://api.deepset.ai",
)

with httpx.AsyncClient() as client:
    deepset_cloud_api = get_deepset_cloud_api(config, client=client)
    files_api = FilesAPI(deepset_cloud_api)
    upload_sessions_api = UploadSessionsAPI(deepset_cloud_api)

    file_service = FilesService(upload_sessions_api, files_api, mocked_aws)


    # your implementation would start here!
    file_service.upload_file_paths(<your  implementation
