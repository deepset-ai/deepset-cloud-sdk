from pathlib import Path
from deepset_cloud_sdk.workflows.async.files import upload_file_paths

upload_file_paths(file_paths=[Path("./tmp/my-file")])
