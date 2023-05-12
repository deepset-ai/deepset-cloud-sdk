from pathlib import Path

from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.sync_client.files import (
    upload_file_paths,
    upload_folder,
    upload_texts,
)

## Example 1: Upload multiple files by providing explicit file paths
## --------------------------------------------------------
## Uploads a list of files to the default workspace.
upload_file_paths(
    workspace_name="my_workspace",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    file_paths=[
        Path("./examples/data/example.txt"),
        Path("./examples/data/example.txt.meta.json"),
        Path("./examples/data/example.pdf"),
    ],
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
)


## Example 2: Upload all files from a folder
## -----------------------------------------
## Uploads all files from a folder to the default workspace.
upload_folder(
    workspace_name="my_workspace",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    folder_path=Path("./examples/data"),
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
)


## Example 3: Upload raw texts
## ---------------------------
## Uploads a list of raw texts to the default workspace.
upload_texts(
    workspace_name="my_workspace",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    dc_files=[
        DeepsetCloudFile(
            name="example.txt",
            text="this is text",
            meta={"key": "value"},  # optional
        )
    ],
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
)
