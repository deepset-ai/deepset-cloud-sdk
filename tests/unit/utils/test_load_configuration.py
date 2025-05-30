import os
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import pytest

from deepset_cloud_sdk._api.config import ENV_FILE_PATH, load_environment


class TestLoadEnvironment:
    """Test the environment loading functionality."""

    @pytest.fixture(autouse=True)
    def clean_env(self) -> Generator[None, None, None]:
        """Fixture to provide a clean environment for tests."""
        original_environ = os.environ.copy()
        os.environ.clear()
        yield
        os.environ.clear()
        os.environ.update(original_environ)

    def test_load_local_env_only(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test loading only local .env file."""
        # Create a temporary local .env file
        local_env = tmp_path / ".env"
        local_env.write_text("API_KEY=local_key\nAPI_URL=local_url\nDEFAULT_WORKSPACE_NAME=local_workspace")

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        # Mock Path.is_file to return True for local .env and False for global
        monkeypatch.setattr(Path, "is_file", lambda self: self == local_env)

        # Mock load_dotenv to actually load the variables into the environment
        def mock_load_dotenv(path: Path, override: bool = True) -> bool:
            os.environ["API_KEY"] = "local_key"
            os.environ["API_URL"] = "local_url"
            os.environ["DEFAULT_WORKSPACE_NAME"] = "local_workspace"
            return True

        monkeypatch.setattr("deepset_cloud_sdk._api.config.load_dotenv", mock_load_dotenv)

        assert load_environment()

    def test_load_global_env_only(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test loading only global .env file."""
        # Create a temporary global .env file
        global_env_dir = tmp_path / "global_config"
        global_env_dir.mkdir()
        global_env = global_env_dir / ".env"
        global_env.write_text("API_KEY=global_key\nAPI_URL=global_url\nDEFAULT_WORKSPACE_NAME=global_workspace")

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        # point mocked global path to global ENV_FILE_PATH definition
        monkeypatch.setattr("deepset_cloud_sdk._api.config.ENV_FILE_PATH", global_env)

        # Mock load_dotenv to actually load the variables into the environment
        def mock_load_dotenv(path: Path, override: bool = True) -> bool:
            os.environ["API_KEY"] = "global_key"
            os.environ["API_URL"] = "global_url"
            os.environ["DEFAULT_WORKSPACE_NAME"] = "global_workspace"
            return True

        monkeypatch.setattr("deepset_cloud_sdk._api.config.load_dotenv", mock_load_dotenv)

        assert load_environment()

    def test_load_both_env_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test loading both local and global .env files."""
        # Create temporary local and global .env files
        local_env = tmp_path / ".env"
        local_env.write_text("API_KEY=local_key\nAPI_URL=local_url\nDEFAULT_WORKSPACE_NAME=local_workspace")
        global_env = tmp_path / "global.env"
        global_env.write_text("API_KEY=global_key\nAPI_URL=global_url\nDEFAULT_WORKSPACE_NAME=global_workspace")

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        monkeypatch.setattr(Path, "is_file", Mock(return_value=True))
        monkeypatch.setattr("deepset_cloud_sdk._api.config.ENV_FILE_PATH", global_env)

        assert load_environment()
        assert os.environ["API_KEY"] == "local_key"
        assert os.environ["API_URL"] == "local_url"
        assert os.environ["DEFAULT_WORKSPACE_NAME"] == "local_workspace"

    def test_global_env_fills_missing_variables(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that global .env variables are available when not defined in local .env."""
        # Create local .env with only API_KEY
        local_env = tmp_path / ".env"
        local_env.write_text("API_KEY=local_key")

        # Create global .env with both API_KEY and API_URL
        global_env_dir = tmp_path / "global_config"
        global_env_dir.mkdir()
        global_env = global_env_dir / ".env"
        global_env.write_text("API_KEY=global_key\nAPI_URL=global_url\nDEFAULT_WORKSPACE_NAME=global_workspace")

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        monkeypatch.setattr("deepset_cloud_sdk._api.config.ENV_FILE_PATH", global_env)

        # Mock is_file to return True for both files
        monkeypatch.setattr(Path, "is_file", lambda self: self in [local_env, global_env])

        assert load_environment()
        # Local API_KEY should take precedence
        assert os.environ["API_KEY"] == "local_key"
        # Global API_URL should be available
        assert os.environ["API_URL"] == "global_url"
        # Global DEFAULT_WORKSPACE_NAME should be available
        assert os.environ["DEFAULT_WORKSPACE_NAME"] == "global_workspace"

    def test_pre_existing_env_vars_take_precedence(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that pre-existing environment variables take precedence over .env files."""
        # Create local .env with API_KEY and API_URL
        local_env = tmp_path / ".env"
        local_env.write_text("API_KEY=local_key\nAPI_URL=local_url\nDEFAULT_WORKSPACE_NAME=local_workspace")

        # Create global .env with different values
        global_env_dir = tmp_path / "global_config"
        global_env_dir.mkdir()
        global_env = global_env_dir / ".env"
        global_env.write_text("API_KEY=global_key\nAPI_URL=global_url\nDEFAULT_WORKSPACE_NAME=global_workspace")

        # Set pre-existing environment variables
        os.environ["API_KEY"] = "pre_existing_key"
        os.environ["API_URL"] = "pre_existing_url"
        os.environ["DEFAULT_WORKSPACE_NAME"] = "pre_existing_workspace"

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        monkeypatch.setattr("deepset_cloud_sdk._api.config.ENV_FILE_PATH", global_env)

        # Mock is_file to return True for both files
        monkeypatch.setattr(Path, "is_file", Mock(return_value=True))

        assert load_environment()
        # Pre-existing values should take precedence
        assert os.environ["API_KEY"] == "pre_existing_key"
        assert os.environ["API_URL"] == "pre_existing_url"
        assert os.environ["DEFAULT_WORKSPACE_NAME"] == "pre_existing_workspace"

    def test_no_env_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test when no .env files exist."""
        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        monkeypatch.setattr(Path, "is_file", Mock(return_value=False))
        mocked_load_dotenv = Mock()
        monkeypatch.setattr("deepset_cloud_sdk._api.config.load_dotenv", mocked_load_dotenv)

        assert not load_environment()
        assert mocked_load_dotenv.call_count == 0

    @pytest.mark.parametrize(
        "missing_var",
        [
            "API_KEY=global_key\nAPI_URL=global_url",
            "API_KEY=global_key\nDEFAULT_WORKSPACE_NAME=global_workspace",
            "API_URL=global_url\nDEFAULT_WORKSPACE_NAME=global_workspace",
        ],
    )
    def test_missing_required_variables(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing_var: str
    ) -> None:
        """Test when required environment variables are missing."""
        # Create a temporary local .env file with only API_KEY
        local_env = tmp_path / ".env"
        local_env.write_text(missing_var)

        monkeypatch.setattr("deepset_cloud_sdk._api.config.Path.cwd", Mock(return_value=tmp_path))
        monkeypatch.setattr(Path, "is_file", lambda self: self == local_env)

        # Mock load_dotenv to actually load the variables into the environment
        def mock_load_dotenv(path: Path, override: bool = True) -> bool:
            for line in missing_var.split("\n"):
                key, value = line.split("=")
                os.environ[key] = value
            return True

        monkeypatch.setattr("deepset_cloud_sdk._api.config.load_dotenv", mock_load_dotenv)

        assert not load_environment()
