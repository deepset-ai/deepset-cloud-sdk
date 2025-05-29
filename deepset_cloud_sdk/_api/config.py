"""Config for loading env variables and setting default values."""

import os
from dataclasses import dataclass

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

ENV_FILE_PATH = os.path.expanduser("~/.deepset-cloud/.env")


def load_environment() -> bool:
    """Load environment variables using a cascading fallback model.

    1. Load local .env file in current directory if it exists
    2. For additional variables, load from global ~/.deepset-cloud/.env
    3. Environment variables can override both

    :return: True if required environment variables were loaded successfully, False otherwise.
    """
    successfully_loaded_env: bool = False
    current_path_env = os.path.join(os.getcwd(), ".env")
    global_env_exists = os.path.isfile(ENV_FILE_PATH)
    local_env_exists = os.path.isfile(current_path_env)

    # First load local config
    if local_env_exists:
        successfully_loaded_env = load_dotenv(current_path_env)
        logger.debug(f"Loaded local .env file at {current_path_env}.")

    # Then load global config only for variables which do not exist in the local .env file
    if global_env_exists:
        global_loaded = load_dotenv(ENV_FILE_PATH, override=False)
        if global_loaded:
            successfully_loaded_env = True
            logger.debug(
                f"Loaded global .env file at {ENV_FILE_PATH} for variables which do not exist "
                "in the local .env file."
            )

    if not successfully_loaded_env:
        logger.warning(
            "No .env files found. Run `deepset-cloud login` to create a global configuration file. "
            "You can also create a custom local .env file in your project directory."
        )
        return successfully_loaded_env

    # Check for required environment variables
    required_vars = ["API_KEY", "API_URL", "DEFAULT_WORKSPACE_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        successfully_loaded_env = False
        logger.warning(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please run `deepset-cloud login` to set up your configuration or set these variables manually."
        )
    else:
        logger.info("Environment variables loaded successfully.")

    return successfully_loaded_env


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
    4. Global .env file in ~/.deepset-cloud/ (only for undefined variables)
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
