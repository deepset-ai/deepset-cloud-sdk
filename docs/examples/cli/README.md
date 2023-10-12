# deepset Cloud CLI
The deepset Cloud CLI is a command-line interface tool that you can use to interact with the deepset Cloud SDK and perform various operations, such as uploading files and folders to your deepset Cloud workspace.

## Installation
To install the deepset Cloud CLI, use `pip`:

```shell
pip install deepset-cloud-sdk
```
## Configuration
Before using the deepset Cloud CLI, log in and provide your credentials. You can do this by running the command:

On MacOS and Linux:

```shell
deepset-cloud login
```
On Windows:

```shell
python -m deepset_cloud_sdk.cli login
```

This command prompts you to enter your API key and default workspace name. Once you provide these details, the CLI stores your credentials in the `~/.deepset-cloud/.env` file. This file is used as the default configuration for subsequent CLI commands.

Alternatively, to use a different environment file for your configuration, you can create an `.env` file in the local directory. Additionally, you have the flexibility to provide the credentials directly as command-line arguments or set them programmatically in your code.

## Usage
You can use the deepset Cloud CLI by running the following command:

On MacOS and Linux:

```shell
deepset-cloud <command>
```

On Windows:

```shell
python -m deepset_cloud_sdk.cli <command>
```

Replace <command> with one of the supported commands. To list all available commands, use the `--help` flag.

## Example Commands

### Upload Files and Folders

You don't have to follow any special folder structure. If there are multiple files with the same name in your folder, they're all uploaded by default. You can change this behavior with the `--write-mode` flag. See the examples below.

This command uploads the file example.txt to your deepset Cloud workspace. 
On MacOS and Linux:

```shell
deepset-cloud upload ./examples/data/example.txt
```

On Windows:

```shell
python -m deepset_cloud_sdk.cli upload ./examples/data/example.txt
```

This command uploads the entire data folder located in the _examples_ directory to your deepset Cloud workspace.
The paths in the examples are relative to the current working directory.

On MacOS and Linux:

```shell
deepset-cloud upload ./examples/data
```
On Windows:
```shell
python -m deepset_cloud_sdk.cli upload ./examples/data
```
To overwrite existing files in your project, use the `--write-mode` flag. For example:

On MacOS and Linux:
```shell
deepset-cloud upload ./examples/data --write-mode OVERWRITE
```
On Windows:
```shell
python -m deepset_cloud_sdk.cli upload ./examples/data --write-mode OVERWRITE
```
This syncs your local files with the files in your deepset Cloud workspace without having to manually delete the files in your workspace.


### Downloading Files from deepset Cloud
This command downloads all files from a workspace to a local directory. For example:

On MacOS and Linux:

```shell
deepset-cloud download --workspace-name <your-workspace-name>
```
On Windows:
```shell
python -m deepset_cloud_sdk.cli download --workspace-name <your-workspace-name>
```

To filter for specific files, use the same filters as for listing files.


### List Files
You can run the `list-files` operation to search files in your deepset Cloud workspace. For example:

On MacOS and Linux:
```shell
deepset-cloud list-files
```
On Windows:
```shell
python -m deepset_cloud_sdk.cli list-files
```
with optional arguments:

```shell
--name "<your-file-name>"  # search by file name
--content "content" # search by file content
--odata-filter "key eq 'value'" # search by odata filter
```

### Support
If you encounter issues or have  questions, reach out to our team on [Discord](https://discord.com/invite/qZxjM4bAHU).

We hope you find the deepset Cloud CLI useful in your projects. Happy coding!
