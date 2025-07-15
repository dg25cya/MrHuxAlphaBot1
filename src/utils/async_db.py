"""Async database utilities."""
from typing import Any, Callable, Awaitable, TypeVar, Coroutine
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session

from src.database import SessionLocal

T = TypeVar('T')

@asynccontextmanager
async def async_db_session():
    """Async context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        await asyncio.to_thread(session.commit)
    except Exception as e:
        await asyncio.to_thread(session.rollback)
        raise
    finally:
        await asyncio.to_thread(session.close)

async def run_db_query(session: Session, query_func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a database query asynchronously.
    
    Args:
        session: SQLAlchemy session
        query_func: Function that executes the query
        *args, **kwargs: Arguments to pass to query_func
    
    Returns:
        Query result
    """
    return await asyncio.to_thread(query_func, session, *args, **kwargs)

def _query_func_get(session: Session, model, id) -> Any:
    """Get an entity by ID."""
    return session.query(model).get(id)

def _query_func_filter(session: Session, model, *args) -> Any:
    """Filter entities."""
    return session.query(model).filter(*args).all()

def _query_func_count(session: Session, model, *args) -> int:
    """Count entities."""
    return session.query(model).filter(*args).count()

def _query_func_commit(session: Session) -> None:
    """Commit the session."""
    session.commit()

async def async_get(session: Session, model, id) -> Any:
    """Get an entity by ID asynchronously."""
    return await run_db_query(session, _query_func_get, model, id)

async def async_filter(session: Session, model, *args) -> Any:
    """Filter entities asynchronously."""
    return await run_db_query(session, _query_func_filter, model, *args)

async def async_count(session: Session, model, *args) -> int:
    """Count entities asynchronously."""
    return await run_db_query(session, _query_func_count, model, *args)

async def async_commit(session: Session) -> None:
    """Commit the session asynchronously."""
    return await run_db_query(session, _query_func_commit)
