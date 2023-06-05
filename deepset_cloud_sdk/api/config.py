"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

ENV_FILE_PATH = os.path.expanduser("~/.deepset-cloud/.env")


def load_environment() -> bool:
    """Load environment variables from the .env file.

    If an .env file exists in the current directory, load the environment variables from there.
    Otherwise, load the environment variables from the .env file in the home directory. You can create this file using the CLI
    by running `deepset-cloud login` in the terminal.

    :return: True if the environment variables were loaded successfully, False otherwise.
    """
    successfully_loded_env: bool = False
    current_path_env = os.path.join(os.getcwd(), ".env")
    if os.path.isfile(current_path_env):
        # Load the environment variables from the .env file in the current directory
        successfully_loded_env = load_dotenv(current_path_env)
        return successfully_loded_env
    else:
        # Load the environment variables from the .env file in the home directory
        successfully_loded_env = load_dotenv(ENV_FILE_PATH)
        return successfully_loded_env


loaded_env_vars = load_environment()
if loaded_env_vars:
    logger.info("Environment variables loaded successfully.")
else:
    logger.warning(
        "No environment variables were loaded from the .env file. Create the .env file and add API_KEY and API_URL there, or run `deepset-cloud login` in the terminal to let SDK create the file for you."
    )

# connection to deepset Cloud
API_URL: str = os.getenv("API_URL", "https://api.cloud.deepset.ai/api/v1")

API_KEY: str = os.getenv("API_KEY", "")

# configuration to use a selectd workspace
DEFAULT_WORKSPACE_NAME: str = os.getenv("DEFAULT_WORKSPACE_NAME", "")


@dataclass
class CommonConfig:
    """Common config for connecting to the deepset Cloud API."""

    api_key: str = API_KEY
    api_url: str = API_URL

    def __post_init__(self) -> None:
        """Validate config."""
        assert (
            self.api_key != ""
        ), "You must set the API_KEY environment variable. Go to [Connections](https://cloud.deepset.ai/settings/connections) in deepset Cloud to get an API key."
        assert self.api_url != "", "API_URL environment variable must be set."

        if self.api_url.endswith("/"):
            self.api_url = self.api_url[:-1]
