"""General Data classes for deepset cloud SDK."""
from dataclasses import dataclass

from click import UUID


@dataclass
class UserInfo:
    """User info data class."""

    user_id: UUID
    given_name: str
    family_name: str
