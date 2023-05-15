"""CLI app for the deepset cloud SDK."""
import os

import typer

from deepset_cloud_sdk.api.config import ENV_FILE_PATH
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


def run_packaged() -> None:
    """Run the packaged CLI app.

    This is the entrypoint for the package to enable running the CLI app using typer.
    """
    cli_app()


if __name__ == "__main__":
    cli_app()
