# Examples

## Upload datasets to deepset Cloud

We provide three different ways to upload datasets:
1. Upload multiple files via explicit file paths
2. Upload all files from a folder
3. Upload raw texts

All three methods have the same parameters:
- workspace_name: str = None
- blocking: bool = True
- timeout_s: int = 300

The parameters api_key and api_url are optional and can be set via environment variables.

The parameter workspace_name is optional and can be set via environment variable.
If no workspace_name is provided, the default workspace is used.

The parameter blocking is optional and can be set to False if you want to upload files and not wait for
deepset Cloud to list the files in the workspace. This can take up to 1 Hour, depending on the size and number
the files.

The parameter timeout_s is optional and can be set to a custom timeout in seconds. The default is 300 seconds.
