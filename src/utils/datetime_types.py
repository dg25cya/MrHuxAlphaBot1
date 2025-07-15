"""SQLite datetime type."""
from sqlalchemy import types


class TZDateTime(types.TypeDecorator):
    """Converts timezone-aware datetimes into SQLite-compatible timestamps."""
    impl = types.DateTime

    def process_bind_param(self, value, dialect) -> None:
        """Convert to UTC before storing."""
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(None)  # Convert to UTC
            value = value.replace(tzinfo=None)  # Remove tzinfo for SQLite
        return value

    def process_result_value(self, value, dialect) -> None:
        """Return naive UTC datetime."""
        return value
