import os
import tempfile
from pathlib import Path
from typing import List

import pytest
from _pytest.monkeypatch import MonkeyPatch

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._api.files import File
from deepset_cloud_sdk._api.upload_sessions import WriteMode
from deepset_cloud_sdk._service.files_service import DeepsetCloudFile, FilesService


@pytest.mark.asyncio
class TestUploadsFileService:
    async def test_direct_upload_path(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            timeout = 120 if "dev.cloud.dpst.dev" in integration_config.api_url else 300

            result = await file_service.upload(
                workspace_name=workspace_name,
                paths=[Path("./tests/test_data/msmarco.10")],
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=timeout,
            )
            assert result.total_files == 10
            assert result.successful_upload_count == 10
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

            names_of_uploaded_files = [
                file.name
                for file in Path("./tests/test_data/msmarco.10").glob("*.txt")
                if not file.name.endswith(".meta.json")
            ]
            # Check the metadata was uploaded correctly
            files: List[File] = []
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                batch_size=11,
                timeout_s=120,
            ):
                files += file_batch

            for file in files:
                if file.name in names_of_uploaded_files:
                    assert (
                        file.meta.get("source") == "msmarco"
                    ), f"Metadata was not uploaded correctly for file '{file.name}': {file.meta}"

    async def test_direct_upload_path_multiple_file_types(
        self, integration_config: CommonConfig, workspace_name: str
    ) -> None:
        async with FilesService.factory(integration_config) as file_service:
            timeout = 120 if "dev.cloud.dpst.dev" in integration_config.api_url else 300

            result = await file_service.upload(
                workspace_name=workspace_name,
                paths=[Path("./tests/test_data/multiple_file_types")],
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=timeout,
            )
            assert result.total_files == 9
            assert result.successful_upload_count == 9
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

            local_file_names: List[str] = [
                file.name
                for file in Path("./tests/test_data/multiple_file_types").glob("*")
                if not file.name.endswith(".meta.json")
            ]

            uploaded_files: List[File] = []
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                batch_size=20,
                timeout_s=120,
            ):
                uploaded_files += file_batch

            uploaded_file_names: List[str] = [file.name for file in uploaded_files]
            for local_file_name in local_file_names:
                assert local_file_name in uploaded_file_names

            for file in uploaded_files:
                if file.name in local_file_names:
                    assert (
                        file.meta.get("source") == "multiple file types"
                    ), f"Metadata was not uploaded correctly for file '{file.name}': {file.meta}"

    async def test_async_upload(
        self, integration_config: CommonConfig, workspace_name: str, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("deepset_cloud_sdk._service.files_service.DIRECT_UPLOAD_THRESHOLD", 1)
        async with FilesService.factory(integration_config) as file_service:
            timeout = 120 if "dev.cloud.dpst.dev" in integration_config.api_url else 300

            result = await file_service.upload(
                workspace_name=workspace_name,
                paths=[Path("./tests/test_data/msmarco.10")],
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=timeout,
            )
            assert result.total_files == 10
            assert result.successful_upload_count == 10
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

            local_file_names: List[str] = [
                file.name
                for file in Path("./tests/test_data/msmarco.10").glob("*.txt")
                if not file.name.endswith(".meta.json")
            ]
            # Check the metadata was uploaded correctly
            uploaded_files: List[File] = []
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                batch_size=30,
                timeout_s=120,
            ):
                uploaded_files += file_batch

        # We already uploaded the same set of files in a previous test, so we expect files to exist twice
        for local_file_name in local_file_names:
            count = sum(1 for uploaded_file in uploaded_files if uploaded_file.name == local_file_name)
            assert count >= 2, f"File '{local_file_name}' does not exist twice in uploaded files"

        for file in uploaded_files:
            if file.name in local_file_names:
                assert (
                    file.meta.get("source") == "msmarco"
                ), f"Metadata was not uploaded correctly for file '{file.name}': {file.meta}"

    async def test_async_upload_multiple_file_types(
        self, integration_config: CommonConfig, workspace_name: str, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("deepset_cloud_sdk._service.files_service.DIRECT_UPLOAD_THRESHOLD", 1)
        async with FilesService.factory(integration_config) as file_service:
            timeout = 120 if "dev.cloud.dpst.dev" in integration_config.api_url else 300

            result = await file_service.upload(
                workspace_name=workspace_name,
                paths=[Path("./tests/test_data/multiple_file_types")],
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=timeout,
            )
            assert result.total_files == 9
            assert result.successful_upload_count == 9
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

            local_file_names: List[str] = [
                file.name
                for file in Path("./tests/test_data/multiple_file_types").glob("*")
                if not file.name.endswith(".meta.json")
            ]

            uploaded_files: List[File] = []
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                batch_size=39,
                timeout_s=120,
            ):
                uploaded_files += file_batch

        # We already uploaded the same set of files in a previous test, so we expect files to exist twice
        for local_file_name in local_file_names:
            count = sum(1 for uploaded_file in uploaded_files if uploaded_file.name == local_file_name)
            assert count >= 2, f"File '{local_file_name}' does not exist twice in uploaded files"

        for file in uploaded_files:
            if file.name in local_file_names:
                assert (
                    file.meta.get("source") == "multiple file types"
                ), f"Metadata was not uploaded correctly for file '{file.name}': {file.meta}"

    async def test_upload_texts(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            files = [
                DeepsetCloudFile("file1", "file1.txt", {"which": 1}),
                DeepsetCloudFile("file2", "file2.txt", {"which": 2}),
                DeepsetCloudFile("file3", "file3.txt", {"which": 3}),
                DeepsetCloudFile("file4", "file4.txt", {"which": 4}),
                DeepsetCloudFile("file5", "file5.txt", {"which": 5}),
            ]
            result = await file_service.upload_texts(
                workspace_name=workspace_name,
                files=files,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )
            assert result.total_files == 5
            assert result.successful_upload_count == 5
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0

    async def test_upload_texts_less_than_session_threshold(
        self, integration_config: CommonConfig, workspace_name: str, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("deepset_cloud_sdk._service.files_service.DIRECT_UPLOAD_THRESHOLD", -1)
        async with FilesService.factory(integration_config) as file_service:
            files = [
                DeepsetCloudFile("file1", "file1.txt", {"which": 1}),
                DeepsetCloudFile("file2", "file2.txt", {"which": 2}),
                DeepsetCloudFile("file3", "file3.txt", {"which": 3}),
                DeepsetCloudFile("file4", "file4.txt", {"which": 4}),
                DeepsetCloudFile("file5", "file5.txt", {"which": 5}),
            ]
            result = await file_service.upload_texts(
                workspace_name=workspace_name,
                files=files,
                blocking=True,
                write_mode=WriteMode.KEEP,
                timeout_s=120,
            )
            assert result.total_files == 10
            assert result.successful_upload_count == 10
            assert result.failed_upload_count == 0
            assert len(result.failed) == 0


@pytest.mark.asyncio
class TestListFilesService:
    async def test_list_all_files(self, integration_config: CommonConfig, workspace_name: str) -> None:
        async with FilesService.factory(integration_config) as file_service:
            file_batches: List[List[File]] = []
            async for file_batch in file_service.list_all(
                workspace_name=workspace_name,
                batch_size=11,
                timeout_s=120,
            ):
                file_batches.append(file_batch)

            assert len(file_batches) >= 2
            assert len(file_batches[0]) == 11
            assert len(file_batches[1]) >= 1


@pytest.mark.asyncio
class TestDownloadFilesService:
    async def test_download_files(self, integration_config: CommonConfig, workspace_name: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            async with FilesService.factory(integration_config) as file_service:
                # cancel download after 5 seconds
                try:
                    await file_service.download(workspace_name=workspace_name, file_dir=tmp_dir, timeout_s=5)
                except Exception:
                    pass
                finally:
                    # test that files were downloaded
                    assert len(os.listdir(tmp_dir)) > 0
