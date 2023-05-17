from pathlib import Path

from deepset_cloud_sdk.workflows.sync_client.files import upload_folder

upload_folder(
    api_key="api_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1OWU0MjFlZi1lODNlLTQ0NzAtOTRlMy0yYjI3ZjhkOGJjZDF8NjI5NzY4NWVmMzdiNTIwMDY4NDU3ODMxIiwiZXhwIjoxNzAxMzQ2OTc1LCJhdWQiOlsiaHR0cHM6Ly9hcGkuZGV2LmNsb3VkLmRwc3QuZGV2Il19.67RJAcMTsCE7nUVwLjWQVh2xfFHpv2LlO4vxvdbs4LE",
    api_url="https://api.dev.cloud.dpst.dev/api/v1",
    workspace_name="sdk_write",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    # folder_path=Path("/Users/rohan/repos/deepset/test-data/downloads/squadv2.1_000_000/txt"),
    folder_path=Path("./tests/test_data/msmarco.10"),
    blocking=True,  # optional, by default True
    timeout_s=300,  # optional, by default 300
    show_progress=False,
)
