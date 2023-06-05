"""General data classes for deepset Cloud SDK."""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class UserInfo:
    """User info data class."""

    user_id: UUID
    given_name: str
    family_name: str


@dataclass
class DeepsetCloudFile:
    """Data class for files in deepset Cloud."""

    text: str
    name: str
    meta: Optional[Dict[str, Any]] = None
