"""Tests for the alert service."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import and_

from src.core.services.alert_service import check_token_alerts, cleanup_old_alerts, get_verdict
from src.models.alert import Alert
from src.models.token import Token
from src.models.token_metrics import TokenMetrics
from src.models.token_score import TokenScore
from src.utils import get_utc_now


@pytest.fixture
def mock_telegram_client():
    """Create a mock Telegram client."""
    mock = AsyncMock()
    mock.send_message = AsyncMock(return_value=MagicMock(id=12345))
    return mock


@pytest.fixture
def test_token(db_session):
    """Create a test token."""
    token = Token(
        address="So11111111111111111111111111111111111111111",
        symbol="TEST",
        name="Test Token"
    )
    db_session.add(token)
    db_session.commit()
    return token


def test_get_verdict():
    """Test verdict generation based on scores."""
    # Low safety score should be AVOID
    low_safety = TokenScore(
        token_id=1,
        safety_composite=40,
        liquidity_composite=80,
        social_composite=80,
        total_score=70,
        calculated_at=datetime.now(timezone.utc)
    )
    assert get_verdict(low_safety) == "AVOID ❌"
    
    # High total score should be HOT BUY
    high_score = TokenScore(
        token_id=1,
        safety_composite=90,
        liquidity_composite=80,
        social_composite=80,
        total_score=85,
        calculated_at=datetime.now(timezone.utc)
    )
    assert get_verdict(high_score) == "HOT BUY 🔥"
    
    # Good but not great should be PROMISING
    good_score = TokenScore(
        token_id=1,
        safety_composite=70,
        liquidity_composite=60,
        social_composite=60,
        total_score=65,
        calculated_at=datetime.now(timezone.utc)
    )
    assert get_verdict(good_score) == "PROMISING ⭐"
    
    # Mediocre scores should be CAUTION
    mediocre = TokenScore(
        token_id=1,
        safety_composite=50,
        liquidity_composite=50,
        social_composite=50,
        total_score=50,
        calculated_at=datetime.now(timezone.utc)
    )
    assert get_verdict(mediocre) == "CAUTION ⚠️"


@pytest.mark.asyncio
async def test_price_increase_alert(db_session, test_token, mock_telegram_client):
    """Test price increase alert generation."""
    # Create previous metrics
    prev_metrics = TokenMetrics(
        token_id=test_token.id,
        price=1.0,
        market_cap=1_000_000,
        volume_24h=100_000,
        liquidity_usd=500_000,
        holder_count=1000,
        buy_tax=1.0,
        sell_tax=1.0,
        created_at=get_utc_now() - timedelta(hours=1)
    )
    db_session.add(prev_metrics)
    
    # Create current metrics with 25% price increase
    current_metrics = TokenMetrics(
        token_id=test_token.id,
        price=1.25,  # 25% increase
        market_cap=1_250_000,
        volume_24h=150_000,  # 50% increase
        liquidity_usd=600_000,
        holder_count=1100,
        buy_tax=1.0,
        sell_tax=1.0,
        created_at=get_utc_now()
    )
    db_session.add(current_metrics)
    
    # Create score
    score = TokenScore(
        token_id=test_token.id,
        liquidity_composite=70.0,
        safety_composite=80.0,
        social_composite=60.0,
        total_score=70.0,
        calculated_at=get_utc_now()
    )
    db_session.add(score)
    db_session.commit()
    
    # Count initial price increase alerts
    initial_count = db_session.query(Alert).filter(Alert.alert_type == "price_increase").count()
    
    # Test alert generation
    await check_token_alerts(test_token, current_metrics, score, db_session, mock_telegram_client)
    
    # Verify only one price increase alert was added
    new_count = db_session.query(Alert).filter(Alert.alert_type == "price_increase").count()
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_volume_spike_alert(db_session, test_token, mock_telegram_client):
    """Test volume spike alert generation."""
    # Create previous metrics
    prev_metrics = TokenMetrics(
        token_id=test_token.id,
        price=1.0,
        market_cap=1_000_000,
        volume_24h=100_000,
        liquidity_usd=500_000,
        holder_count=1000,
        buy_tax=1.0,
        sell_tax=1.0,
        created_at=get_utc_now() - timedelta(hours=1)
    )
    db_session.add(prev_metrics)
    
    # Create current metrics with 100% volume increase
    current_metrics = TokenMetrics(
        token_id=test_token.id,
        price=1.0,
        market_cap=1_000_000,
        volume_24h=200_000,  # 100% increase
        liquidity_usd=500_000,
        holder_count=1000,
        buy_tax=1.0,
        sell_tax=1.0,
        created_at=get_utc_now()
    )
    db_session.add(current_metrics)
    
    # Create score
    score = TokenScore(
        token_id=test_token.id,
        liquidity_composite=70.0,
        safety_composite=80.0,
        social_composite=60.0,
        total_score=70.0,
        calculated_at=get_utc_now()
    )
    db_session.add(score)
    db_session.commit()
    
    # Count initial volume spike alerts
    initial_count = db_session.query(Alert).filter(Alert.alert_type == "volume_spike").count()
    
    # Test alert generation
    await check_token_alerts(test_token, current_metrics, score, db_session, mock_telegram_client)
    
    # Verify only one volume spike alert was added
    new_count = db_session.query(Alert).filter(Alert.alert_type == "volume_spike").count()
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_high_score_alert(db_session, test_token, mock_telegram_client):
    """Test high score alert generation."""
    # Create metrics with safety data
    metrics = TokenMetrics(
        token_id=test_token.id,
        price=1.0,
        market_cap=1_000_000,
        volume_24h=100_000,
        liquidity_usd=500_000,
        holder_count=1000,
        buy_tax=2.0,
        sell_tax=2.0,
        raw_metrics={
            "contract_verified": True,
            "owner_renounced": True,
            "liquidity_locked": True,
            "is_honeypot": False
        },
        created_at=get_utc_now()
    )
    db_session.add(metrics)
    
    # Create high score
    score = TokenScore(
        token_id=test_token.id,
        liquidity_composite=90.0,
        safety_composite=85.0,
        social_composite=80.0,
        total_score=85.0,  # Above MIN_SCORE_THRESHOLD
        calculated_at=get_utc_now()
    )
    db_session.add(score)
    db_session.commit()
    
    # Count initial high score alerts
    initial_count = db_session.query(Alert).filter(Alert.alert_type == "high_score").count()
    
    # Test alert generation
    await check_token_alerts(test_token, metrics, score, db_session, mock_telegram_client)
    
    # Verify only one high score alert was added
    new_count = db_session.query(Alert).filter(Alert.alert_type == "high_score").count()
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_alert_cleanup(db_session):
    """Test cleanup of old alerts."""
    # Create some old alerts
    old_alerts = [
        Alert(
            token_id=1,
            alert_type="test",
            created_at=get_utc_now() - timedelta(days=31)
        ),
        Alert(
            token_id=1,
            alert_type="test",
            created_at=get_utc_now() - timedelta(days=35)
        )
    ]
    db_session.add_all(old_alerts)
    
    # Create a recent alert
    recent_alert = Alert(
        token_id=1,
        alert_type="test",
        created_at=get_utc_now() - timedelta(days=5)
    )
    db_session.add(recent_alert)
    db_session.commit()
    
    # Run cleanup
    deleted = await cleanup_old_alerts(db_session)
    assert deleted == 2
    
    # Verify only old alerts were deleted
    remaining = db_session.query(Alert).count()
    assert remaining == 1
