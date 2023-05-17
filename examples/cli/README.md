# deepset Cloud CLI
The deepset Cloud CLI is a command-line interface tool that you can use to interact with the deepset Cloud SDK and perform various operations, such as uploading files and folders to your deepset Cloud workspace.

## Installation
To install the deepset Cloud CLI, use `pip`:

```shell
pip3 install deepset-cloud-sdk
```
## Configuration
Before using the deepset Cloud CLI, log in and provide your credentials. You can do this by running the command:

```shell
deepset-cloud-cli login
```

This command prompts you to enter your API key and default workspace name. Once you provide these details, the CLI stores your credentials in the `~/.deepset-cloud-cli/.env` file. This file is used as the default configuration for subsequent CLI commands.

Alternatively, to use a different environment file for your configuration, you can create an `.env` file in the local directory. Additionally, you have the flexibility to provide the credentials directly as command-line arguments or set them programmatically in your code.

## Usage
You can use the deepset Cloud CLI by running the following command:
```shell
deepset-cloud-cli <command>
```
Replace <command> with one of the supported commands. To list all available commands, run: `deepset-cloud-cli --help`.

## Example Commands

### Upload Files and Folders
This command uploads the file example.txt to your deepset Cloud workspace.

```shell
deepset-cloud-cli upload ./examples/data
```
This command uploads the entire data folder, located in the examples directory, to your deepset Cloud workspace.
Note that the paths provided in the above examples are relative to the current working directory.

If you want to overwrite existing files in your project, you can use the `--write-mode` flag. For example:
```shell
deepset-cloud-cli upload ./examples/data --write-mode OVERWRITE
```
This syncs your local files with the files in your deepset Cloud workspace without having to manually delete the files in your workspace.


### List files
You can run the `list-files` operation to search files in your deepset Cloud workspace. For example:
```shell
deepset-cloud-cli list-files
```
with optional arguments:
```shell
--name "<your-file-name>"  # search by file name
--content "content" # search by file content
--odata-filter "key eq 'value'" # search by odata filter
```

### Documentation
For more information and detailed usage instructions, see the deepset Cloud SDK documentation.

### Support
If you encounter any issues or have any questions, feel free to reach out to our team on [discord](https://discord.com/invite/qZxjM4bAHU).

We hope you find the deepset Cloud CLI useful in your projects. Happy coding!
