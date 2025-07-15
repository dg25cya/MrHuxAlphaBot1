"""Test configuration and fixtures."""
import json
import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import TypeDecorator, DateTime
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import aiohttp
from typing import AsyncGenerator, Dict, Any

from src.models.base import Base
from src.config.settings import get_settings
from src.main import app
from src.api.dependencies import get_db

settings = get_settings()


def _enable_sqlite_json():
    """Enable JSON support for SQLite."""
    import sqlite3
    sqlite3.register_adapter(dict, json.dumps)
    sqlite3.register_adapter(list, json.dumps)
    sqlite3.register_converter("JSON", json.loads)


class TZDateTime(TypeDecorator):
    """SQLite-compatible timezone-aware datetime type."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=timezone.utc)
        return value


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    _enable_sqlite_json()
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Register custom types
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("json_extract", 2, lambda x, y: None)
    
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Create a test database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    """Get test client."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def mock_aiohttp_session() -> AsyncGenerator[Mock, None]:
    """Mock aiohttp session for API client tests."""
    mock_session = Mock(spec=aiohttp.ClientSession)
    mock_response = Mock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "success"})
    mock_session.get.return_value.__aenter__.return_value = mock_response
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    yield mock_session


@pytest.fixture
def mock_websocket() -> Mock:
    """Mock WebSocket connection."""
    mock_ws = Mock(spec=["accept", "send_json", "receive_json", "close"])
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_json = AsyncMock(return_value={"type": "ping"})
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_token_data() -> Dict[str, Any]:
    """Mock token data for tests."""
    return {
        "address": "testaddress123",
        "price": 1.0,
        "market_cap": 1000000,
        "volume": 100000,
        "liquidity": 50000,
        "holders": 1000,
        "score": {
            "safety": 80,
            "momentum": 70,
            "overall": 75
        },
        "validation": {
            "is_valid": True,
            "checks": {
                "contract_safety": {"passed": True, "required": True},
                "liquidity": {"passed": True, "required": True}
            }
        },
        "momentum": {
            "score": 3.5,
            "hype_level": "high",
            "mention_count": 50,
            "avg_sentiment": 0.8
        }
    }


@pytest.fixture(autouse=True, scope="function")
def reset_db():
    from src.database import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
