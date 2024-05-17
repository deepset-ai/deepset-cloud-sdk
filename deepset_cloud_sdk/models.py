"""General data classes for deepset Cloud SDK."""
import json
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from uuid import UUID


@dataclass
class UserInfo:
    """User info data class."""

    user_id: UUID
    given_name: str
    family_name: str


class DeepsetCloudFileBase:  # pylint: disable=too-few-public-methods
    """Base class for deepset Cloud files."""

    def __init__(self, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param meta: The file's metadata
        """
        self.name = name
        self.meta = meta

    @abstractmethod
    def content(self) -> Union[str, bytes]:
        """Return content."""
        raise NotImplementedError

    def meta_as_string(self) -> str:
        """Return metadata as a string."""
        if self.meta:
            return json.dumps(self.meta)

        return json.dumps({})


class DeepsetCloudFile(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for text files in deepset Cloud."""

    def __init__(self, text: str, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param text: The text content of the file
        :param meta: The file's metadata
        """
        super().__init__(name, meta)
        self.text = text

    def content(self) -> str:
        """
        Return the content of the file.

        :return: The text of the file.
        """
        return self.text


# Didn't want to cause breaking changes in the DeepsetCloudFile class, though it
# is technically the same as the below, the naming of the text field will be confusing
# for users that are uploading anything other than text.


class DeepsetCloudFileBytes(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for uploading files of any valid type in deepset Cloud."""

    def __init__(self, file_bytes: bytes, name: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param file_bytes: The content of the file represented in bytes
        :param meta: The file's metadata
        """
        super().__init__(name, meta)
        self.file_bytes = file_bytes

    def content(self) -> bytes:
        """
        Return the content of the file in bytes.

        :return: The content of the file in bytes.
        """
        return self.file_bytes
