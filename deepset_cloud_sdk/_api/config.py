"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass
from pathlib import Path

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

ENV_FILE_PATH = Path.home() / ".deepset-cloud" / ".env"


def load_environment() -> bool:
    """Load environment variables using a cascading fallback model.

    1. Load local .env file in current directory if it exists
    2. Load from global ~/.deepset-cloud/.env to supplement local .env file
    3. Environment variables can override both local and global .env files

    :return: True if required environment variables were loaded successfully, False otherwise.
    """
    current_path_env = Path.cwd() / ".env"
    local_loaded = current_path_env.is_file() and load_dotenv(current_path_env)
    global_loaded = ENV_FILE_PATH.is_file() and load_dotenv(ENV_FILE_PATH, override=False)

    if local_loaded:
        logger.info(f"Environment variables successfully loaded from local .env file at {current_path_env}.")
    if global_loaded:
        if local_loaded:
            logger.info(f"Loaded global .env file at {ENV_FILE_PATH} to supplement local .env file.")
        else:
            logger.info(f"Environment variables successfully loaded from global .env file at {ENV_FILE_PATH}.")

    if not (local_loaded or global_loaded):
        logger.warning(
            "No .env files found. Run `deepset-cloud login` to create a global configuration file. "
            "You can also create a custom local .env file in your project directory."
        )
        return False

    # Check for required environment variables
    required_vars = ["API_KEY", "API_URL", "DEFAULT_WORKSPACE_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Run `deepset-cloud login` to set up your configuration or set these variables "
            "manually in your .env file."
        )
        return False

    return True


loaded_env_vars = load_environment()

# connection to deepset AI Platform
API_URL: str = os.getenv("API_URL", "https://api.cloud.deepset.ai/api/v1")

API_KEY: str = os.getenv("API_KEY", "")

# configuration to use a selected workspace
DEFAULT_WORKSPACE_NAME: str = os.getenv("DEFAULT_WORKSPACE_NAME", "")

ASYNC_CLIENT_TIMEOUT: int = int(os.getenv("ASYNC_CLIENT_TIMEOUT", "300"))


@dataclass
class CommonConfig:
    """Common config for connecting to the deepset AI Platform.

    Configuration is loaded in the following order of precedence:
    1. Explicit parameters passed to this class
    2. Environment variables
    3. Local .env file in project root
    4. Global .env file in ~/.deepset-cloud/ (supplements local .env)
    5. Built-in defaults
    """

    api_key: str = API_KEY
    api_url: str = API_URL
    safe_mode: bool = False

    def __post_init__(self) -> None:
        """Validate config."""
        assert (
            self.api_key != ""
        ), "You must set the API_KEY environment variable. Go to [API Keys](https://cloud.deepset.ai/settings/api-keys) in deepset AI Platform to get an API key."
        assert self.api_url != "", "API_URL environment variable must be set."

        if self.api_url.endswith("/"):
            self.api_url = self.api_url[:-1]
