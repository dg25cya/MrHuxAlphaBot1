"""Tests for token scoring service."""
from datetime import datetime, timedelta, timezone
import pytest

from src.core.services.scoring import (
    calculate_liquidity_scores,
    calculate_safety_scores,
    calculate_social_scores,
    calculate_token_score
)
from src.models.token import Token
from src.models.token_metrics import TokenMetrics
from src.models.token_score import TokenScore
from src.models.mention import TokenMention
from src.models.group import MonitoredGroup
from src.utils import get_utc_now


def test_liquidity_scores():
    """Test calculation of liquidity-related scores."""
    metrics = TokenMetrics(
        liquidity_usd=1_000_000,  # $1M liquidity
        market_cap=5_000_000,    # $5M market cap
        volume_24h=50_000,       # $50K volume
        created_at=datetime.now(timezone.utc)
    )
    
    scores = calculate_liquidity_scores(metrics)
    
    assert scores["liquidity_score"] == 100  # Max score for $1M+ liquidity
    assert scores["market_cap_score"] == 50   # Mid score for reasonable market cap
    assert scores["volume_score"] == 50       # Mid score for reasonable volume
    assert 0 <= scores["composite"] <= 100


def test_safety_scores():
    """Test calculation of safety-related scores."""
    now = datetime.now(timezone.utc)
    
    # Test good metrics
    good_metrics = TokenMetrics(
        buy_tax=2,
        sell_tax=2,
        created_at=now,
        raw_metrics={
            "contract_verified": True,
            "owner_renounced": True,
            "liquidity_locked": True,
            "is_honeypot": False
        }
    )
    
    good_scores = calculate_safety_scores(good_metrics)
    assert good_scores["contract_safety_score"] == 100
    assert good_scores["ownership_score"] == 100
    assert good_scores["liquidity_lock_score"] == 100
    assert good_scores["honeypot_risk_score"] == 100
    assert 0 <= good_scores["composite"] <= 100  # Reduced by tax penalties
    
    # Test bad metrics
    bad_metrics = TokenMetrics(
        buy_tax=10,
        sell_tax=10,
        created_at=now,
        raw_metrics={
            "contract_verified": False,
            "owner_renounced": False,
            "liquidity_locked": False,
            "is_honeypot": True
        }
    )
    
    bad_scores = calculate_safety_scores(bad_metrics)
    assert bad_scores["contract_safety_score"] == 0
    assert bad_scores["ownership_score"] == 0
    assert bad_scores["liquidity_lock_score"] == 0
    assert bad_scores["honeypot_risk_score"] == 0
    assert bad_scores["composite"] == 0


def test_social_scores(db_session):
    """Test calculation of social metrics scores."""
    # Create test data
    token = Token(address="So11111111111111111111111111111111111111111")
    db_session.add(token)
    
    group1 = MonitoredGroup(
        group_id=1,
        name="High Weight Group",
        weight=1.0
    )
    group2 = MonitoredGroup(
        group_id=2,
        name="Low Weight Group",
        weight=0.5
    )
    db_session.add_all([group1, group2])
    db_session.commit()
    
    # Add some mentions in last 24h
    now = get_utc_now()
    mentions = [
        TokenMention(
            token_id=token.id,
            group_id=group1.id,
            message_id=1,
            message_text="Great token!",
            mentioned_at=now - timedelta(hours=1),
            sentiment=0.8
        ),
        TokenMention(
            token_id=token.id,
            group_id=group2.id,
            message_id=2,
            message_text="Looking good",
            mentioned_at=now - timedelta(hours=2),
            sentiment=0.5
        ),
        # Old mention that shouldn't count
        TokenMention(
            token_id=token.id,
            group_id=group1.id,
            message_id=3,
            message_text="Old message",
            mentioned_at=now - timedelta(days=2),
            sentiment=0.9
        )
    ]
    db_session.add_all(mentions)
    db_session.commit()
    
    scores = calculate_social_scores(token.id, db_session)
    
    assert scores["mention_frequency_score"] == 20  # 2 recent mentions * 10
    assert 70 <= scores["source_reliability_score"] <= 80  # Average of 1.0 and 0.5, scaled to 100
    assert 80 <= scores["sentiment_score"] <= 90  # Average of 0.8 and 0.5, scaled from [-1,1] to [0,100]
    assert 0 <= scores["composite"] <= 100


@pytest.mark.asyncio
async def test_total_scoring(db_session):
    """Test end-to-end token scoring."""
    # Create test token and metrics
    token = Token(address="So11111111111111111111111111111111111111111")
    db_session.add(token)
    
    now = get_utc_now()
    metrics = TokenMetrics(
        token_id=token.id,
        price=1.0,
        market_cap=5_000_000,
        volume_24h=50_000,
        liquidity_usd=1_000_000,
        holder_count=1000,
        buy_tax=2,
        sell_tax=2,
        raw_metrics={
            "contract_verified": True,
            "owner_renounced": True,
            "liquidity_locked": True,
            "is_honeypot": False,
            "risk_level": "LOW"
        },
        created_at=now
    )
    db_session.add(metrics)
    db_session.commit()
    
    # Calculate score
    score = await calculate_token_score(token, metrics, db_session)
    
    assert score is not None
    assert score.token_id == token.id
    assert score.calculated_at is not None
    assert score.calculated_at.tzinfo is not None  # Verify timezone awareness
    assert 0 <= score.total_score <= 100
    assert score.raw_metrics == metrics.raw_metrics
    
    # Verify composites
    assert 0 <= score.liquidity_composite <= 100
    assert 0 <= score.safety_composite <= 100
    assert 0 <= score.social_composite <= 100
    
    # Verify component scores
    assert 0 <= score.liquidity_score <= 100
    assert 0 <= score.market_cap_score <= 100
    assert 0 <= score.volume_score <= 100
    assert 0 <= score.contract_safety_score <= 100
    assert 0 <= score.ownership_score <= 100
    assert 0 <= score.liquidity_lock_score <= 100
    assert 0 <= score.honeypot_risk_score <= 100
    assert 0 <= score.mention_frequency_score <= 100
    assert 0 <= score.source_reliability_score <= 100
    assert 0 <= score.sentiment_score <= 100
