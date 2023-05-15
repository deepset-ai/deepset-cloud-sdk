# Examples

## Upload files to deepset Cloud

You can upload files in three different ways:
1. Upload multiple files by providing explicit file paths.
2. Upload all files from a folder.
3. Upload raw text.

All three methods have the same parameters:
- `workspace_name`: str = None
    Optional. Specifies the deepset Cloud workspace where you want to upload the files. You can set it through environment variable. If you don't provide any value, the files are uploaded to the `default` workspace.
- `blocking`: bool = True
    Optional. Specifies if you want to wait until your files are listed in deepset Cloud. This can take up to one hour, depending on the size and number of files.
- `timeout_s`: int = 300
    Optional. A custom timeout for file upload in seconds.
- `api_key`: str = None
    Optional. The API key to deepset Cloud. You can configure it through an environment variable.
- `api_url`: str = None
    Optional. The production URL. It's useful for running tests against a dev environment or your own domain. You can configure it through an environment variable. For other cases, you can just ignore it.
