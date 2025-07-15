"""Tests for bot command handlers."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from telethon import events
from src.core.telegram.commands import setup_command_handlers
from src.models.group import MonitoredGroup
from src.models.token import Token
from src.models.token_metrics import TokenMetrics
from src.models.token_score import TokenScore
from src.models.mention import TokenMention
from src.utils import get_utc_now

@pytest.fixture
def mock_event():
    """Create a mock event object."""
    event = AsyncMock()
    event.reply = AsyncMock()
    event.pattern_match = MagicMock()
    return event

@pytest.fixture
def mock_client():
    """Create a mock Telegram client."""
    client = AsyncMock()
    client.on = MagicMock()
    return client

@pytest.mark.asyncio
async def test_start_command(mock_event, mock_client):
    """Test the /start command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
      # Call the first handler directly
    for call in mock_client.on.call_args_list:
        pattern = call[0][0]
        if isinstance(pattern, events.NewMessage) and pattern.pattern == r'/start':
            handler = pattern.callback
            await handler(mock_event)
            break
    
    # Verify response
    mock_event.reply.assert_called_once()
    response = mock_event.reply.call_args[0][0]
    assert "👋 Hi!" in response
    assert "/monitor" in response
    assert "/analyze" in response

@pytest.mark.asyncio
async def test_monitor_command(mock_event, mock_client, db_session):
    """Test the /monitor command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
    
    # Get the /monitor command handler
    handler = mock_client.on.call_args_list[1][0][0].callback
    
    # Setup test data
    group_id = -1001234567890
    mock_event.pattern_match.group.return_value = str(group_id)
    
    # Call the handler
    with patch('src.core.telegram.commands.db_session', return_value=db_session):
        await handler(mock_event)
    
    # Verify group was added
    group = db_session.query(MonitoredGroup).filter(
        MonitoredGroup.group_id == group_id
    ).first()
    assert group is not None
    assert group.group_id == group_id
    
    # Verify response
    mock_event.reply.assert_called_once_with(
        f"Started monitoring group {group_id}"
    )

@pytest.mark.asyncio
async def test_stats_command(mock_event, mock_client, db_session):
    """Test the /stats command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
    
    # Get the /stats command handler
    handler = mock_client.on.call_args_list[3][0][0].callback
    
    # Setup test data
    group = MonitoredGroup(group_id=-1001234567890, added_at=get_utc_now())
    token = Token(
        address="So11111111111111111111111111111111111111112",
        first_seen_at=get_utc_now(),
        last_updated_at=get_utc_now()
    )
    db_session.add(group)
    db_session.add(token)
    db_session.flush()
    
    mention = TokenMention(
        token_id=token.id,
        group_id=group.id,
        message_id=1,
        message_text="Test mention",
        mentioned_at=get_utc_now()
    )
    db_session.add(mention)
    db_session.commit()
    
    # Call the handler
    with patch('src.core.telegram.commands.db_session', return_value=db_session):
        await handler(mock_event)
    
    # Verify response
    mock_event.reply.assert_called_once()
    response = mock_event.reply.call_args[0][0]
    assert "Monitored Groups: 1" in response
    assert "Total Tokens: 1" in response
    assert "Total Mentions: 1" in response

@pytest.mark.asyncio
async def test_analyze_command(mock_event, mock_client, db_session):
    """Test the /analyze command."""
    # Setup command handlers
    await setup_command_handlers(mock_client)
    
    # Get the /analyze command handler
    handler = mock_client.on.call_args_list[4][0][0].callback
    
    # Setup test data
    token_address = "So11111111111111111111111111111111111111112"
    mock_event.pattern_match.group.return_value = token_address
    
    token = Token(
        address=token_address,
        first_seen_at=get_utc_now(),
        last_updated_at=get_utc_now()
    )
    db_session.add(token)
    db_session.flush()
    
    metrics = TokenMetrics(
        token_id=token.id,
        market_cap=1000000.0,
        volume_24h=100000.0,
        holder_count=1000,
        created_at=get_utc_now()
    )
    score = TokenScore(
        token_id=token.id,
        liquidity_score=8.5,
        safety_score=7.0,
        social_score=6.5,
        total_score=7.3,
        created_at=get_utc_now()
    )
    db_session.add(metrics)
    db_session.add(score)
    db_session.commit()
    
    # Mock token validation and scoring
    with patch('src.core.telegram.commands.validate_token') as mock_validate, \
         patch('src.core.telegram.commands.calculate_token_score') as mock_score, \
         patch('src.core.telegram.commands.db_session', return_value=db_session):
        
        mock_validate.return_value = MagicMock(is_valid=True)
        mock_score.return_value = score
        await handler(mock_event)
    
    # Verify response
    mock_event.reply.assert_called_once()
    response = mock_event.reply.call_args[0][0]
    assert token_address[:8] in response
    assert "Total Score: 7.3" in response
    assert "Market Cap: $1,000,000.00" in response
    assert "24h Volume: $100,000.00" in response
    assert "Holders: 1,000" in response
