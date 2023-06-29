"""The CLI for the deepset Cloud SDK."""
import json
import os
from typing import List, Optional
from uuid import UUID

import typer
from tabulate import tabulate

from deepset_cloud_sdk.__about__ import __version__
from deepset_cloud_sdk._api.config import DEFAULT_WORKSPACE_NAME, ENV_FILE_PATH
from deepset_cloud_sdk.workflows.sync_client.files import (
    get_upload_session as sync_get_upload_session,
)
from deepset_cloud_sdk.workflows.sync_client.files import list_files as sync_list_files
from deepset_cloud_sdk.workflows.sync_client.files import (
    list_upload_sessions as sync_list_upload_sessions,
)
from deepset_cloud_sdk.workflows.sync_client.files import upload

cli_app = typer.Typer(pretty_exceptions_show_locals=False)

# cli commands
cli_app.command()(upload)


@cli_app.command()
def login() -> None:
    """Log in to deepset Cloud. This command creates an .ENV file with your deepset Cloud API key and the default workspace used for all operations.

    Run this command before performing any tasks in deepset Cloud using the SDK or CLI, unless you already created the .ENV file.

    Example:
    `deepset-cloud login`

    This prompts you to provide your deepset Cloud API key and workspace name.
    """
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
    """Log out of deepset Cloud. This command deletes the .ENV file created during login.

    Example:
    `deepset-cloud logout`
    """
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
    """List files that exist in the specified deepset Cloud workspace.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from. Uses the workspace from the .EVN file by default.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    :param batch_size: Batch size to use for the file list.
    :param timeout_s: The timeout for this request, in seconds.

    Example:
    `deepset-cloud list-files --batch-size 10`

    Example using an odata filter to show only files whose category is "news":
    `deepset-cloud list-files --odata-filter 'category eq "news"'`
    """
    try:
        headers = [
            "file_id",
            "url",
            "name",
            "size",
            "created_at",
            "meta",
        ]  # Assuming the first row contains the headers
        for files in sync_list_files(
            api_key, api_url, workspace_name, name, content, odata_filter, batch_size, timeout_s
        ):
            table = tabulate(files, headers, tablefmt="grid")  # type: ignore
            typer.echo(table)
            if len(files) > 0:
                prompt_input = typer.prompt("Print more results ?", default="y")
                if prompt_input != "y":
                    break
    except TimeoutError:
        typer.echo("Command timed out.")


@cli_app.command()
def list_upload_sessions(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    is_expired: Optional[bool] = False,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    batch_size: int = 10,
    timeout_s: int = 300,
) -> None:
    """List the details of all upload sessions for the specified workspace, including closed sessions.

    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from. Uses the workspace from the .EVN file by default.
    :param is_expired: Whether to list expired upload sessions.
    :param batch_size: Batch size to use for the file list.
    :param timeout_s: Timeout in seconds for the API requests.

    Example:
    `deepset-cloud list-upload-sessions --workspace-name default`
    """
    headers: List[str] = ["session_id", "created_by", "created_at", "expires_at", "write_mode", "status"]
    try:
        for upload_sessions in sync_list_upload_sessions(
            api_key=api_key,
            api_url=api_url,
            workspace_name=workspace_name,
            is_expired=is_expired,
            batch_size=batch_size,
            timeout_s=timeout_s,
        ):
            table = tabulate(
                [
                    {
                        "session_id": str(el.session_id),
                        "created_by": f"{el.created_by.given_name} {el.created_by.family_name}",
                        "created_at": str(el.created_at),
                        "expires_at": str(el.expires_at),
                        "write_mode": el.write_mode.name,
                        "status": el.status.name,
                    }
                    for el in upload_sessions
                ],
                dict(enumerate(headers)),  # type: ignore
                tablefmt="grid",
            )
            typer.echo(table)
            if len(upload_sessions) > 0:
                prompt_input = typer.prompt("Print more results?", default="y")
                if prompt_input != "y":
                    break
    except TimeoutError:
        typer.echo("Command timed out. Please try again later.")


@cli_app.command()
def get_upload_session(
    session_id: UUID,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
) -> None:  # noqa: D400, D205
    """Fetch an upload session from deepset Cloud. This method is useful for checking
    the status of an upload session after uploading files to deepset Cloud.

    :param session_id: ID of the upload session whose status you want to check.
    :param api_key: deepset Cloud API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace where you upload your files. Uses the workspace from the .EVN file by default.

    Example:
    `deepset-cloud get-upload-session --workspace-name default`
    """
    session = sync_get_upload_session(
        session_id=session_id, api_key=api_key, api_url=api_url, workspace_name=workspace_name
    )
    typer.echo(
        json.dumps(
            {
                "session_id": str(session.session_id),
                "expires_at": str(session.expires_at),
                "documentation_url": str(session.documentation_url),
                "ingestion_status": {
                    "failed_files": session.ingestion_status.failed_files,
                    "finished_files": session.ingestion_status.finished_files,
                },
            },
            indent=4,
        )
    )


def version_callback(value: bool) -> None:
    """Show the SDK version and exit.

    :param value: Value of the version option.

    Example:
    `deepset-cloud --version`
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

    Example:
    `deepset cloud run-packaged`
    """
    cli_app()


if __name__ == "__main__":
    cli_app()
