"""Time-related utility functions."""
from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)

def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO format."""
    return dt.isoformat()

def parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO format timestamp to datetime."""
    return datetime.fromisoformat(timestamp)

def time_since(dt: datetime) -> float:
    """Get seconds elapsed since given datetime."""
    return (datetime.now(timezone.utc) - dt).total_seconds()

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"
