---
title: Synchronous Client
excerpt: A synchronous client for the Deepset Cloud API.
category: ID
slug: sync_client
order: 0
hidden: false
---

<a id="files"></a>

# Module files

Sync client for files workflow.

<a id="files.upload_file_paths"></a>

#### upload\_file\_paths

```python
def upload_file_paths(file_paths: List[Path],
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
- `blocking`: Whether to wait for the files to be uploaded and listed in deepset Cloud.
- `timeout_s`: Timeout in seconds for the `blocking` parameter`.

<a id="files.upload"></a>

#### upload

```python
def upload(paths: List[Path],
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

- `paths`: Path to the folder to upload. If the folder contains unsupported file types, they're skipped.
deepset Cloud supports TXT and PDF files.
- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to upload the files to.
- `blocking`: Whether to wait for the files to be uploaded and displayed in deepset Cloud.
- `timeout_s`: Timeout in seconds for the `blocking` parameter.

<a id="files.upload_texts"></a>

#### upload\_texts

```python
def upload_texts(files: List[DeepsetCloudFile],
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
- `blocking`: Whether to wait for the files to be uploaded and listed in deepset Cloud.
- `timeout_s`: Timeout in seconds for the `blocking` parameter.

<a id="files.get_upload_session"></a>

#### get\_upload\_session

```python
def get_upload_session(
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
- `workspace_name`: Name of the workspace to upload the files to.

<a id="files.list_files"></a>

#### list\_files

```python
def list_files(api_key: Optional[str] = None,
               api_url: Optional[str] = None,
               workspace_name: str = DEFAULT_WORKSPACE_NAME,
               name: Optional[str] = None,
               content: Optional[str] = None,
               odata_filter: Optional[str] = None,
               batch_size: int = 100,
               timeout_s: int = 300) -> Generator[List[File], None, None]
```

List files in deepset Cloud.

WARNING: This only works for workspaces with up to 1000 files.

**Arguments**:

- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to list the files from.
- `name`: Name of the file to odata_filter for.
- `content`: Content of the file to odata_filter for.
- `odata_filter`: odata_filter to apply to the file list.
- `batch_size`: Batch size to use for the file list.
- `timeout_s`: Timeout in seconds for the API requests.

<a id="files.list_upload_sessions"></a>

#### list\_upload\_sessions

```python
def list_upload_sessions(
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        workspace_name: str = DEFAULT_WORKSPACE_NAME,
        is_expired: Optional[bool] = False,
        batch_size: int = 100,
        timeout_s: int = 300
) -> Generator[List[UploadSessionDetail], None, None]
```

List files in deepset Cloud.

WARNING: This only works for workspaces with up to 1000 files.

**Arguments**:

- `api_key`: deepset Cloud API key to use for authentication.
- `api_url`: API URL to use for authentication.
- `workspace_name`: Name of the workspace to list the files from.
- `is_expired`: Name of the file to odata_filter for.
- `batch_size`: Batch size to use for the file list.
- `timeout_s`: Timeout in seconds for the API requests.
