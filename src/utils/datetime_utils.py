"""Utility functions for datetime operations."""
from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(timezone.utc)
