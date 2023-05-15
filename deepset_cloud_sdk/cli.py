"""CLI app for the deepset cloud SDK."""
import typer

from deepset_cloud_sdk.workflows.sync_client.files import (
    upload_file_paths,
    upload_folder,
)

cli_app = typer.Typer()

# cli commands
cli_app.command()(upload_file_paths)
cli_app.command()(upload_folder)


def run_packaged() -> None:
    """Run the packaged CLI app.

    This is the entrypoint for the package to enable running the CLI app using typer.
    """
    cli_app()


if __name__ == "__main__":
    cli_app()
