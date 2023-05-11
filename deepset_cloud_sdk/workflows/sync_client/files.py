import asyncio
from pathlib import Path
from typing import List, Optional

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_file_paths as async_upload_file_paths,
)
from deepset_cloud_sdk.workflows.async_client.files import (
    upload_folder as async_upload_folder,
)


def upload_file_paths(
    file_paths: List[Path],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    asyncio.run(
        async_upload_file_paths(
            file_paths=file_paths,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            blocking=blocking,
            timeout_s=timeout_s,
        )
    )


def upload_folder(
    folder_path: Path,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    blocking: bool = True,
    timeout_s: int = 300,
) -> None:
    asyncio.run(
        async_upload_folder(
            folder_path=folder_path,
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            blocking=blocking,
            timeout_s=timeout_s,
        )
    )
