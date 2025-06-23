"""Utility functions for working with datetime objects."""

from datetime import datetime


def from_isoformat(date_str: str) -> datetime:
    """Parse a date string in ISO 8601 format and returns a datetime object.

    Our new Pydantic 2.0 API returns with the `Z` suffix, but the old one returns with `+00:00`
    Python versions < 3.12 don't support the `Z` suffix, so we need to replace it with `+00:00`
    """
    date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)
