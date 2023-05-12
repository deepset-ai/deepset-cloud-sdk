"""General Data classes for deepset cloud SDK."""
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
    """Dataclass for files in deepsetCloud."""

    text: str
    name: str
    meta: Optional[Dict[str, Any]] = None
