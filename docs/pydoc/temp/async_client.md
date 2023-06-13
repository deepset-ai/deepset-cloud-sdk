---
title: Asynchronous Client
excerpt: An asynchronous client for the Deepset Cloud API.
category: ID
slug: async_client
order: 0
hidden: false
---

<a id="files"></a>

# Module files

This module contains async functions for uploading files and folders to deepset Cloud.

<a id="files.list_files"></a>

#### list\_files

```python
async def list_files(api_key: Optional[str] = None,
                     api_url: Optional[str] = None,
                     workspace_name: str = DEFAULT_WORKSPACE_NAME,
                     name: Optional[str] = None,
                     content: Optional[str] = None,
                     odata_filter: Optional[str] = None,
                     batch_size: int = 100,
                     timeout_s: int = 300) -> AsyncGenerator[List[File], None]
```

List all files in a workspace.

**Arguments**:

- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to list the files from.
- `batch_size`: Batch size for the listing.

**Returns**:

List of files.

<a id="files.list_upload_sessions"></a>

#### list\_upload\_sessions

```python
async def list_upload_sessions(
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        workspace_name: str = DEFAULT_WORKSPACE_NAME,
        is_expired: Optional[bool] = None,
        batch_size: int = 100,
        timeout_s: int = 300
) -> AsyncGenerator[List[UploadSessionDetail], None]
```

List all files in a workspace.

**Arguments**:

- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to list the files from.
- `is_expired`: Whether to list expired upload sessions.
- `batch_size`: Batch size for the listing.
- `timeout_s`: Timeout in seconds for the API requests.

**Returns**:

List of files.

<a id="files.get_upload_session"></a>

#### get\_upload\_session

```python
async def get_upload_session(
        session_id: UUID,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        workspace_name: str = DEFAULT_WORKSPACE_NAME) -> UploadSessionStatus
```

Get the status of an upload session.

**Arguments**:

- `session_id`: ID of the upload session to get the status for.
- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to list the files from.

**Returns**:

List of files.

<a id="files.upload_file_paths"></a>

#### upload\_file\_paths

```python
async def upload_file_paths(file_paths: List[Path],
                            api_key: Optional[str] = None,
                            api_url: Optional[str] = None,
                            workspace_name: str = DEFAULT_WORKSPACE_NAME,
                            write_mode: WriteMode = WriteMode.KEEP,
                            blocking: bool = True,
                            timeout_s: int = 300,
                            show_progress: bool = True) -> None
```

Upload files to deepset Cloud.

**Arguments**:

- `file_paths`: List of file paths to upload.
- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to upload the files to.
- `blocking`: Whether to wait for the upload to finish.
- `timeout_s`: Timeout in seconds for the upload.

<a id="files.upload"></a>

#### upload

```python
async def upload(paths: List[Path],
                 api_key: Optional[str] = None,
                 api_url: Optional[str] = None,
                 workspace_name: str = DEFAULT_WORKSPACE_NAME,
                 write_mode: WriteMode = WriteMode.KEEP,
                 blocking: bool = True,
                 timeout_s: int = 300,
                 show_progress: bool = True,
                 recursive: bool = False) -> None
```

Upload a folder to deepset Cloud.

**Arguments**:

- `paths`: Path to the folder to upload. If the folder contains unsupported files, they're skipped
during the upload. Supported file formats are TXT and PDF.
- `api_key`: API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to upload the files to.
- `blocking`: Whether to wait for the upload to finish.
- `timeout_s`: Timeout in seconds for the upload.

<a id="files.upload_texts"></a>

#### upload\_texts

```python
async def upload_texts(files: List[DeepsetCloudFile],
                       api_key: Optional[str] = None,
                       api_url: Optional[str] = None,
                       workspace_name: str = DEFAULT_WORKSPACE_NAME,
                       write_mode: WriteMode = WriteMode.KEEP,
                       blocking: bool = True,
                       timeout_s: int = 300,
                       show_progress: bool = True) -> None
```

Upload texts to deepset Cloud.

**Arguments**:

- `files`: List of DeepsetCloudFiles to upload.
- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to upload the files to.
- `blocking`: Whether to wait for the files to be listed and displayed in deepset Cloud.
This may take a couple of minutes.
- `timeout_s`: Timeout in seconds for the `blocking` parameter.
