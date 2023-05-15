"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

ENV_FILE_PATH = os.path.expanduser("~/.deepset-cloud-cli/.env")


def load_environment() -> bool:
    """Load environment variables from .env file.

    If a .env file is present in the current directory, load the environment variables from there.
    Otherwise, load the environment variables from the .env file in the home directory that can be created using the CLI.
    To create the .env file in the home directory, run `deepset-cloud-cli login` in the terminal.

    :return: True if the environment variables were loaded successfully, False otherwise
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
    logger.info("Environment variables loaded successfully")
else:
    logger.info(
        "No environment variables loaded from .env file. API_KEY and API_URL need to be set manually. If you dont wan't to set them manually, run `deepset-cloud-cli login` in the terminal."
    )

# connection to deepset Cloud
API_URL: str = os.getenv("API_URL", "https://api.cloud.deepset.ai/")
API_KEY: str = os.getenv("API_KEY", "")

# configuration to use a selectd workspace
DEFAULT_WORKSPACE_NAME: str = os.getenv("DEFAULT_WORKSPACE_NAME", "")


@dataclass
class CommonConfig:
    """Common config for connecting to Deepset Cloud API."""

    api_key: str = API_KEY
    api_url: str = API_URL

    def __post_init__(self) -> None:
        """Validate config."""
        assert (
            self.api_key != ""
        ), "API_KEY environment variable must be set. Please visit https://cloud.deepset.ai/settings/connections to get an API key."
        assert self.api_url != "", "API_URL environment variable must be set"
