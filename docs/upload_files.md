# Upload Files

Uploading with SDK is the fastest way if you have many files. It uses sessions under the hood. That means, you create a session and then upload files to this session. Each session has an ID and you can check its status. The upload starts when you close a session. If you leave a session open, it expires after 24 hours.

After your files are uploaded, it can take a while for them to be listed in deepset Cloud. This means that if you deployed a pipeline, you may need to wait a while for it to run on the newly uploaded files.

You can use the CLI or the SDK Python methods to upload your files.

To upload files:
1. Log in to the sdk: `deepset-cloud login`.
2. When prompted, paste your deepset Cloud API key.
3. Type the name of the deepset Cloud workspace you want to set as default for all operations.
4. Choose if you want to use the CLI or a Python script to upload:
    - To upload files from a folder using CLI, run: `deepset-cloud upload <path to the upload folder>`
    - To upload files from a folder using a Python script, create the script and run it. Here's an example you can use: 
    ```
    from pathlib import Path
    from deepset_cloud_sdk.service.files_service import DeepsetCloudFile
    from deepset_cloud_sdk.workflows.sync_client.files import upload
    
    ## Uploads all files from a given path
    upload(
    paths=[Path("<your_path_to_the_upload_folder>")],
    blocking=True,  # waits until the files are displayed in deepset Cloud,
                    # this may take a couple of minutes
    timeout_s=300,  # the timeout for the `blocking` parameter in number of seconds
    show_progress=True,  # shows the progress bar
    recursive=True,  # uploads files from all subfolders as well
    )

    ```

For more examples, see [CLI examples](/examples/cli/README.md) and [SDK examples](/examples/sdk/README.md).

# Metadata

To add metadata to your files, create one metadata file for each TXT or PDF file you upload. The metadata file must be a JSON with the same name as the file whose metadata it contains and the extension `meta.json`.

For example, if you're uploading a file called `example.txt`, the metadata file should be called `example.txt.meta.json`. If you're uploading a file called `example.pdf`, the metadata file should be `example.pdf.meta.json`.

The format your metadata in your metadata files should follow is: `{"meta_key1": "value1", "meta_key2": "value2"}`. See the [example metadata file](/examples/data/example.txt.meta.json).