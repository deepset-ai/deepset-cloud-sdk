import os
from unittest.mock import Mock, patch

from deepset_cloud_sdk._api.config import ENV_FILE_PATH, load_environment


def test_load_environment_from_local_env() -> None:
    current_cwd = os.getcwd()
    with patch("deepset_cloud_sdk._api.config.os") as mocked_os:
        mocked_os.path.join.return_value = current_cwd + "/tests/data/.fake-env"
        mocked_os.path.isfile.return_value = True
        assert load_environment()


@patch("deepset_cloud_sdk._api.config.load_dotenv")
def test_load_environment_with_login_credentials(mocked_load_dotenv: Mock) -> None:
    with patch("deepset_cloud_sdk._api.config.os") as mocked_os:
        mocked_os.path.isfile.return_value = False
        assert load_environment()
        mocked_load_dotenv.assert_called_once_with(ENV_FILE_PATH)
