"""Tests for alert management commands."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.telegram.commands import setup_command_handlers
from src.models.alert import Alert
from src.models.token import Token
from src.utils import get_utc_now

@pytest.fixture
def mock_event():
    """Create a mock event object."""
    event = AsyncMock()
    event.reply = AsyncMock()
    return event

@pytest.fixture
def mock_client():
    """Create a mock Telegram client."""
    client = AsyncMock()
    client.on = MagicMock()
    return client

@pytest.mark.asyncio
async def test_alerts_command(mock_event, mock_client, db_session):
    """Test the /alerts command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
    
    # Get the /alerts command handler
    handler = None
    for call in mock_client.on.call_args_list:
        if call[0][0].pattern == r'/alerts':
            handler = call[0][0].callback
            break
            
    assert handler is not None
    
    # Create test data
    token = Token(
        address="So11111111111111111111111111111111111111112",
        first_seen_at=get_utc_now(),
        last_updated_at=get_utc_now()
    )
    db_session.add(token)
    db_session.flush()
    
    alert1 = Alert(
        token_id=token.id,
        alert_type="price_increase",
        message="Test alert 1",
        created_at=get_utc_now()
    )
    alert2 = Alert(
        token_id=token.id,
        alert_type="volume_spike",
        message="Test alert 2",
        created_at=get_utc_now() - timedelta(hours=12)
    )
    old_alert = Alert(
        token_id=token.id,
        alert_type="high_score",
        message="Old alert",
        created_at=get_utc_now() - timedelta(days=2)
    )
    
    db_session.add(alert1)
    db_session.add(alert2)
    db_session.add(old_alert)
    db_session.commit()
    
    # Call the handler
    with patch('src.core.telegram.commands.db_session', return_value=db_session):
        await handler(mock_event)
    
    # Verify response
    mock_event.reply.assert_called_once()
    response = mock_event.reply.call_args[0][0]
    assert "Recent Alerts" in response
    assert "price_increase" in response
    assert "volume_spike" in response
    assert "high_score" not in response  # Too old
    assert token.address[:8] in response

@pytest.mark.asyncio
async def test_clearalerts_command(mock_event, mock_client, db_session):
    """Test the /clearalerts command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
    
    # Get the /clearalerts command handler
    handler = None
    for call in mock_client.on.call_args_list:
        if call[0][0].pattern == r'/clearalerts':
            handler = call[0][0].callback
            break
            
    assert handler is not None
    
    # Create test data
    token = Token(
        address="So11111111111111111111111111111111111111112",
        first_seen_at=get_utc_now(),
        last_updated_at=get_utc_now()
    )
    db_session.add(token)
    db_session.flush()
    
    # Create some old and new alerts
    old_alert1 = Alert(
        token_id=token.id,
        alert_type="test",
        message="Old alert 1",
        created_at=get_utc_now() - timedelta(days=10)
    )
    old_alert2 = Alert(
        token_id=token.id,
        alert_type="test",
        message="Old alert 2",
        created_at=get_utc_now() - timedelta(days=8)
    )
    new_alert = Alert(
        token_id=token.id,
        alert_type="test",
        message="New alert",
        created_at=get_utc_now()
    )
    
    db_session.add(old_alert1)
    db_session.add(old_alert2)
    db_session.add(new_alert)
    db_session.commit()
    
    # Call the handler
    with patch('src.core.telegram.commands.db_session', return_value=db_session):
        await handler(mock_event)
    
    # Verify response
    mock_event.reply.assert_called_once()
    response = mock_event.reply.call_args[0][0]
    assert "Cleaned up 2 old alerts" in response
    
    # Verify alerts were marked as deleted
    old_alerts = db_session.query(Alert).filter(
        Alert.created_at < get_utc_now() - timedelta(days=7)
    ).all()
    assert all(alert.is_deleted for alert in old_alerts)
    
    # Verify new alert was not deleted
    new_alerts = db_session.query(Alert).filter(
        Alert.created_at >= get_utc_now() - timedelta(days=7)
    ).all()
    assert all(not alert.is_deleted for alert in new_alerts)
