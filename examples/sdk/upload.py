from pathlib import Path

from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
from deepset_cloud_sdk.workflows.sync_client.files import upload, upload_texts

## Example 1: Upload all files from a folder
## -----------------------------------------
## Uploads all files from a folder to the default workspace.
upload(
    workspace_name="my_workspace",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    paths=[Path("./examples/data")],
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
)


## Example 2: Upload raw texts
## ---------------------------
## Uploads a list of raw texts to the default workspace.
upload_texts(
    workspace_name="my_workspace",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    files=[
        DeepsetCloudFile(
            name="example.txt",
            text="this is text",
            meta={"key": "value"},  # optional
        )
    ],
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
)
