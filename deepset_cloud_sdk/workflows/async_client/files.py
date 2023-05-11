import asyncio
from pathlib import Path
from typing import List, Optional
from deepset_cloud_sdk.api.config import API_KEY, API_URL, DEFAULT_WORKSPACE_NAME, CommonConfig
from deepset_cloud_sdk.service.files_service import FilesService
from deepset_cloud_sdk.api.config import CommonConfig


async def upload_file_paths(
    file_paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    config = CommonConfig(api_key=api_key or API_KEY, api_url=api_url or API_URL)
    async with FilesService.factory(config) as file_service:
        await file_service.upload_file_paths(
            workspace_name=workspace_name, file_paths=file_paths, blocking=blocking, timeout_s=timeout_s
        )
