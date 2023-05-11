from pathlib import Path
from deepset_cloud_sdk.workflows.sync_client.files import upload_file_paths
from _pytest.monkeypatch import MonkeyPatch


def test_upload_file_paths(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("deepset_cloud_sdk.workflows.async_client.files", "upload_file_paths", None)
    upload_file_paths(
        file_paths=[Path("./tests/data/example.txt")],
    )
