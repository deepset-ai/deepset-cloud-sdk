# Overview

Uploading with SDK is the fastest way if you have many files. It uses sessions under the hood. That means, you create a session and then upload files to this session. Each session has an ID and you can check its status. The upload starts when you close a session. If you leave a session open, it expires after 24 hours.

After your files are uploaded, it can take a while for them to be listed in deepset Cloud. This means that if you deployed a pipeline, you may need to wait a while for it to run on the newly uploaded files.

You can use the CLI or the SDK Python methods to upload your files.

## Folder Structure

You don't need to follow any specific folder structure. If your folder contains files with the same name, all these files are uploaded, by default. You can set the `--write-mode` to overwrite the files, keep them all, or fail the upload. For more information, see [CLI examples](/examples/cli/README.md) and [SDK examples](/examples/sdk/README.md).

# Upload Files

## Upload text files:

By default it is allowed to upload .txt and .pdf files. See below to upload different file types.

1. Log in to the sdk: `deepset-cloud login` (MacOS and Linux) or `python -m deepset_cloud_sdk.cli login` (Windows).
2. When prompted, paste your deepset Cloud API key.
3. Type the name of the deepset Cloud workspace you want to set as default for all operations.
4. Choose if you want to use the CLI or a Python script to upload:
    - To upload files from a folder using CLI, run: `deepset-cloud upload <path to the upload folder>` (MacOS and Linux) or `python -m deepset_cloud_sdk.cli upload <path to the upload folder>` (On Windows)
    - To upload files from a folder using a Python script, create the script and run it. Here's an example you can use:

    ```python
    from pathlib import Path
    from deepset_cloud_sdk.workflows.sync_client.files import upload

    ## Uploads all txt and pdf files from a given path
    upload(
    paths=[Path("<your_path_to_the_upload_folder>")],
    blocking=True,  # waits until the files are displayed in deepset Cloud,
                    # this may take a couple of minutes
    timeout_s=300,  # the timeout for the `blocking` parameter in number of seconds
    show_progress=True,  # shows the progress bar
    recursive=True,  # uploads text files from all subfolders as well
    )
    ```

## Upload other file types

Deepset Cloud currently supports uploading : .csv, .docx, .html, .json, .md, .txt, .pdf, .pptx, .xlsx and .xml.


    ```python
    from pathlib import Path
    from deepset_cloud_sdk.workflows.sync_client.files import upload

    ## Uploads supported files from a given path
    upload(
    paths=[Path("<your_path_to_the_upload_folder>")],
    blocking=True,
    timeout_s=300,
    show_progress=True,
    recursive=True,
    desired_file_types=[ # list of desired file types to upload
        ".csv", ".docx", ".html", ".json", ".md", ".txt", ".pdf", ".pptx", ".xlsx", ".xml"
    ]
    )
    ```

For more examples, see [CLI examples](/examples/cli/README.md) and [SDK examples](/examples/sdk/README.md).

# Metadata

To add metadata to your files, create one metadata file for each file you upload. The metadata file must be a JSON with the same name as the file whose metadata it contains and the extension `meta.json`.

For example, if you're uploading a file called `example.txt`, the metadata file should be called `example.txt.meta.json`. If you're uploading a file called `example.pdf`, the metadata file should be `example.pdf.meta.json`.

The format your metadata in your metadata files should follow is: `{"meta_key1": "value1", "meta_key2": "value2"}`. See the [example metadata file](/examples/data/example.txt.meta.json).
