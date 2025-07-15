"""SQLite JSON type for testing environment."""
import json
from typing import Any, Optional, Union

from sqlalchemy import TypeDecorator, Text

__all__ = ["SQLiteJSON"]


class SQLiteJSON(TypeDecorator):
    """Enables JSON storage by encoding/decoding on the fly."""

    impl = Text

    cache_ok = True

    def process_bind_param(self, value: Optional[Union[dict, list]], dialect: Any) -> Optional[str]:
        """Convert Python dict/list to JSON string for storage."""
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Union[dict, list]]:
        """Convert stored JSON string back to Python dict/list."""
        if value is not None:
            return json.loads(value)
        return None
