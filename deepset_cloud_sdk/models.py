"""General data classes for deepset Cloud SDK."""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
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
    def content(self) -> bytes:
        """
        An abstract method that will enable sub classes to give custom implementations of content.
        """
        raise NotImplementedError


class DeepsetCloudFile(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for text files in deepset Cloud."""

    def __init__(self, name: str, text: str, meta: Optional[Dict[str, Any]] = None):
        """
        Initialize DeepsetCloudFileBase.

        :param name: The file name
        :param text: The text content of the file
        :param meta: The file's metadata
        """
        super().__init__(name, meta)
        self.text = text

    def content(self) -> bytes:
        """
        Returns the content of the file in bytes

        :return: The text of the file in bytes.
        """
        return bytes(self.text, "utf-8")


# Didn't want to cause breaking changes in the DeepsetCloudFile class, though it
# is technically the same as the below, the naming of the text field will be confusing
# for users that are uploading anything other than text.


class DeepsetCloudFileBytes(DeepsetCloudFileBase):  # pylint: disable=too-few-public-methods
    """Data class for uploading files of any valid type in deepset Cloud."""

    def __init__(self, name: str, file_bytes: bytes, meta: Optional[Dict[str, Any]] = None):
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
        Returns the content of the file in bytes

        :return: The content of the file in bytes.
        """

        return self.file_bytes
