"""API dependencies."""
from typing import Generator
from sqlalchemy.orm import Session
from src.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
