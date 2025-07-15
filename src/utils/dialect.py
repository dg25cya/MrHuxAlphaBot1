"""Database utilities for handling different database dialects."""
from sqlalchemy.dialects.postgresql import JSONB

from src.utils.sqlite_json import SQLiteJSON


def get_json_type() -> None:
    """Get the appropriate JSON type based on the dialect."""
    try:
        from sqlalchemy import create_engine
        engine = create_engine('sqlite:///:memory:')
        if engine.dialect.name == 'sqlite':
            return SQLiteJSON
    except Exception as e:
        pass
    return JSONB
