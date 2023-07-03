# Examples

## Upload files to deepset Cloud

You can upload files in three different ways:
1. Upload multiple files by providing explicit file paths.
2. Upload all files from a folder.
3. Upload raw text.

For uploading files from your local machine to deepset Cloud, you can use `upload`.

To preprocess text and upload the preprocessed text to deepset Cloud, you can use the `upload_text` method. This method accepts a list of `DeepsetCloudFiles` metadata and file name as input, and uploads the text to deepset Cloud.
```python
DeepsetCloudFile(
    name="example.txt",
    text="this is text",
    meta={"key": "value"},
)
```
