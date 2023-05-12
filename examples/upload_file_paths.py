from pathlib import Path

from deepset_cloud_sdk.workflows.sync_client.files import upload_file_paths

upload_file_paths(file_paths=[Path("./tmp/my-file")])
