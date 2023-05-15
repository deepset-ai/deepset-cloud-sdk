# deepset Cloud CLI
The deepset Cloud CLI is a command-line interface tool that allows you to interact with the deepset Cloud SDK and perform various operations, such as uploading files and folders to your deepset Cloud workspace.

## Installation
To install the deepset Cloud CLI, you can use `pip`:

```shell
pip3 install deepset-cloud-sdk
```

## Configuration
The deepset Cloud CLI requires certain environment variables to be set in order to function properly. These environment variables can be defined in an .env file in the root directory of your project. The required variables are as follows:

```shell
# .env file
API_KEY=<your-api-key>
DEFAULT_WORKSPACE_NAME=<your-workspace>
```
Alternatively, you can provide these variables in different ways, such as passing them as command-line arguments or setting them directly in your code.

## Usage
Once you have installed the deepset Cloud CLI and configured the necessary environment variables, you can run it from the console using the following command:

```shell
deepset_cloud_cli <command>
```
Replace <command> with one of the supported commands. Currently, the supported commands are:

upload-folder: Uploads a file or a folder to your deepset Cloud workspace.
Example Commands
Here are a couple of example commands that demonstrate how to use the deepset Cloud CLI:

```shell
deepset_cloud_cli upload-folder ./examples/data/example.txt
```
This command uploads the file example.txt to your deepset Cloud workspace.

```shell
deepset_cloud_cli upload-folder "./examples/data"
```
This command uploads the entire data folder, located in the examples directory, to your deepset Cloud workspace.

Please note that the paths provided in the above examples are relative to the current working directory.

### Documentation
For more information and detailed usage instructions, please refer to the deepset Cloud SDK documentation.

###Support
If you encounter any issues or have any questions, please feel free to reach out to our team on [discord](https://discord.com/invite/qZxjM4bAHU).

We hope you find the deepset Cloud CLI useful in your projects. Happy coding!
