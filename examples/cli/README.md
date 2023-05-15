# deepset Cloud CLI
The deepset Cloud CLI is a command-line interface tool that allows you to interact with the deepset Cloud SDK and perform various operations, such as uploading files and folders to your deepset Cloud workspace.

## Installation
To install the deepset Cloud CLI, you can use `pip`:

```shell
pip3 install deepset-cloud-sdk
```
## Configuration
Before using the deepset Cloud CLI, you need to log in and provide your credentials. You can do this by running the following command:

```shell
deepset-cloud-cli login
```

This command will prompt you to enter your API key and default workspace name. Once you provide these details, the CLI will store your credentials securely in the ~/.deepset-cloud-cli/.env file. This file will be used as the default configuration for subsequent CLI commands.

Alternatively, if you want to use a different environment file for your configuration, you can create an `.env` file in the local directory.
Additionally, you have the flexibility to provide the credentials directly as command-line arguments or set them programmatically in your code, instead of using the environment file. This can be useful in certain scenarios or for automation purposes.


## Usage
Once you have installed the deepset Cloud CLI and configured the necessary environment variables, you can run it from the console using the following command:

```shell
deepset-cloud-cli <command>
```
Replace <command> with one of the supported commands. Currently, the supported commands are:

upload-folder: Uploads a file or a folder to your deepset Cloud workspace.
Example Commands
Here are a couple of example commands that demonstrate how to use the deepset Cloud CLI:

```shell
deepset-cloud-cli upload-folder ./examples/data/example.txt
```
This command uploads the file example.txt to your deepset Cloud workspace.

```shell
deepset-cloud-cli upload-folder "./examples/data"
```
This command uploads the entire data folder, located in the examples directory, to your deepset Cloud workspace.

Please note that the paths provided in the above examples are relative to the current working directory.

### Documentation
For more information and detailed usage instructions, please refer to the deepset Cloud SDK documentation.

###Support
If you encounter any issues or have any questions, please feel free to reach out to our team on [discord](https://discord.com/invite/qZxjM4bAHU).

We hope you find the deepset Cloud CLI useful in your projects. Happy coding!
