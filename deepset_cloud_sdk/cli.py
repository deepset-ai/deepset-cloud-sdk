"""The CLI for the deepset Cloud SDK."""
import os
from typing import Optional

import typer
from tabulate import tabulate

from deepset_cloud_sdk.__about__ import __version__
from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME, ENV_FILE_PATH
from deepset_cloud_sdk.workflows.sync_client.files import list_files as sync_list_files
from deepset_cloud_sdk.workflows.sync_client.files import upload

cli_app = typer.Typer(pretty_exceptions_show_locals=False)

# cli commands
cli_app.command()(upload)


@cli_app.command()
def login() -> None:
    """Log in to deepset Cloud."""
    typer.echo("Log in to deepset Cloud")
    passed_api_key = typer.prompt("Your deepset Cloud API_KEY", hide_input=True)
    passed_default_workspace_name = typer.prompt("Your DEFAULT_WORKSPACE_NAME", default="default")

    # connect to prod by default. You can change this behaviour by modifying the API_URL
    # in the stored env file or by passing the API_URL as an argument to the CLI
    api_url = "https://api.cloud.deepset.ai/api/v1"
    env_content = f"API_KEY={passed_api_key}\nAPI_URL={api_url}\nDEFAULT_WORKSPACE_NAME={passed_default_workspace_name}"

    os.makedirs(os.path.dirname(ENV_FILE_PATH), exist_ok=True)
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as env_file:
        env_file.write(env_content)

    typer.echo(f"{ENV_FILE_PATH} created successfully!")


@cli_app.command()
def logout() -> None:
    """Log out of deepset Cloud."""
    typer.echo("Log out of deepset Cloud")
    config_file_exists = os.path.exists(ENV_FILE_PATH)
    if not config_file_exists:
        typer.echo("You are not logged in. Nothing to do!")
        return
    os.remove(ENV_FILE_PATH)
    typer.echo(f"{ENV_FILE_PATH} removed successfully.")


@cli_app.command()
def list_files(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    content: Optional[str] = None,
    name: Optional[str] = None,
    odata_filter: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    batch_size: int = 10,
    timeout_s: int = 300,
) -> None:
    """List files in deepset Cloud.

    A CLI method to list files that exist in deepset Cloud.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    :param batch_size: Batch size to use for the file list.
    """
    headers = ["file_id", "url", "name", "size", "created_at", "meta"]  # Assuming the first row contains the headers
    for files in sync_list_files(api_key, api_url, workspace_name, name, content, odata_filter, batch_size, timeout_s):
        table = tabulate(files, headers, tablefmt="grid")  # type: ignore
        typer.echo(table)
        if len(files) > 0:
            prompt_input = typer.prompt("Print more results ?", default="y")
            if prompt_input != "y":
                break


def version_callback(value: bool) -> None:
    """Show the version and exit.

    :param value: Value of the version option.
    """
    if value:
        typer.echo(f"deepset Cloud SDK version: {__version__}")
        raise typer.Exit()


@cli_app.callback()
def main(
    _: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show the SDK version and exit."
    )
) -> None:  # noqa
    """The CLI for the deepset Cloud SDK."""


def run_packaged() -> None:
    """Run the packaged CLI.

    This is the entrypoint for the package to enable running the CLI using typer.
    """
    cli_app()


if __name__ == "__main__":
    cli_app()
