"""CLI app for the deepset cloud SDK."""
import os
from typing import Optional

import typer
from typing_extensions import Annotated

from deepset_cloud_sdk.api.config import DEFAULT_WORKSPACE_NAME, ENV_FILE_PATH
from deepset_cloud_sdk.workflows.sync_client.files import list_files as sync_list_files
from deepset_cloud_sdk.workflows.sync_client.files import (
    upload_file_paths,
    upload_folder,
)

cli_app = typer.Typer()

# cli commands
cli_app.command()(upload_file_paths)
cli_app.command()(upload_folder)


@cli_app.command()
def login() -> None:
    """Login to the deepset cloud."""
    typer.echo("Login to the deepset cloud")
    passed_api_key = typer.prompt("Your API_KEY", hide_input=True)
    passed_api_url = typer.prompt("Your API_URL", default="https://api.cloud.deepset.ai/api/v1/")
    passed_default_workspace_name = typer.prompt("Your DEFAULT_WORKSPACE_NAME", default="default")

    env_content = (
        f"API_KEY={passed_api_key}\nAPI_URL={passed_api_url}\nDEFAULT_WORKSPACE_NAME={passed_default_workspace_name}"
    )

    os.makedirs(os.path.dirname(ENV_FILE_PATH), exist_ok=True)
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as env_file:
        env_file.write(env_content)

    typer.echo(f"{ENV_FILE_PATH} created successfully!")


@cli_app.command()
def list_files(
    api_key: Annotated[Optional[str], typer.Option()],
    api_url: Annotated[Optional[str], typer.Option()],
    name: Annotated[Optional[str], typer.Option()],
    content: Annotated[Optional[str], typer.Option()],
    odata_filter: Optional[str] = None,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    batch_size: int = 100,
    timeout_s: int = 300,
) -> None:
    """List files in the Deepset Cloud.

    CLI method to list files in the Deepset Cloud.

    :param api_key: API key to use for authentication.
    :param api_url: API URL to use for authentication.
    :param workspace_name: Name of the workspace to list the files from.
    :param name: Name of the file to odata_filter for.
    :param content: Content of the file to odata_filter for.
    :param odata_filter: odata_filter to apply to the file list.
    :param batch_size: Batch size to use for the file list.
    """
    files = sync_list_files(
        api_key=api_key,
        api_url=api_url,
        workspace_name=workspace_name,
        name=name,
        content=content,
        odata_filter=odata_filter,
        batch_size=batch_size,
        timeout_s=timeout_s,
    )
    typer.echo(" created_at  \t size \t name ")
    for file in files:
        typer.echo(f" {file.created_at}  \t {file.size} \t {file.name} ")


def run_packaged() -> None:
    """Run the packaged CLI app.

    This is the entrypoint for the package to enable running the CLI app using typer.
    """
    cli_app()


if __name__ == "__main__":
    cli_app()
