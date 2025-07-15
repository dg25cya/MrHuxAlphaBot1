"""Database initialization and session management."""
from contextlib import contextmanager
from typing import Generator, List, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings

settings = get_settings()

# Create engine
engine = create_engine(str(settings.database_url))

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> None:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def get_token_performance(session: Session) -> List[Dict[str, Any]]:
    """Get current performance metrics for all tokens."""
    result = session.execute(text("SELECT * FROM token_performance"))
    return [dict(row._mapping) for row in result]


def get_alert_summary(session: Session) -> List[Dict[str, Any]]:
    """Get alert summary for all tokens."""
    result = session.execute(text("SELECT * FROM alert_summary"))
    return [dict(row._mapping) for row in result]


def get_token_performance_by_symbol(session: Session, symbol: str) -> Dict[str, Any]:
    """Get current performance metrics for a specific token."""
    result = session.execute(
        text("SELECT * FROM token_performance WHERE symbol = :symbol"),
        {"symbol": symbol}
    )
    row = result.first()
    return dict(row._mapping) if row else None
