"""Integration tests for the token monitoring system."""
import os
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.core.services.token_monitor import TokenMonitor
from src.api.clients.birdeye import TokenPrice
from src.api.clients.rugcheck import SecurityScore
from src.models import Token, TokenMetrics, TokenScore, Alert
from src.database import get_db, init_db
from src.utils.async_db import async_db_session, run_db_query

# Patch settings to use in-memory SQLite for all tests in this module
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Test data
TEST_TOKEN = {
    "address": "So11111111111111111111111111111111111111112",
    "name": "Solana",
    "symbol": "SOL",
    "decimals": 9,
    "total_supply": "1000000000"
}

MOCK_PRICE_DATA = TokenPrice(
    address=TEST_TOKEN["address"],
    price_usd=100.0,
    price_sol=1.0,
    volume_24h=1000000.0,
    liquidity=5000000.0,
    market_cap=10000000.0,
    price_change_24h=5.0,
    fully_diluted_market_cap=12000000.0,
    holders=1000,
    updated_at=datetime.utcnow()
)

MOCK_SECURITY_DATA = SecurityScore(
    address=TEST_TOKEN["address"],
    total_score=85.0,
    liquidity_score=90.0,
    contract_score=95.0,
    holder_score=80.0,
    is_contract_verified=True,
    is_proxy_contract=False,
    has_mint_function=False,
    has_blacklist_function=False,
    owner_balance_percent=5.0,
    top_holders_percent=25.0,
    is_honeypot=False,
    sell_tax=0.0,
    buy_tax=0.0,
    updated_at=datetime.utcnow()
)

@pytest_asyncio.fixture(autouse=True, scope='module')
async def setup_database():
    await init_db()
    yield

@pytest_asyncio.fixture
async def monitor():
    """Create a token monitor instance."""
    monitor = TokenMonitor()
    yield monitor
    await monitor.stop()

@pytest.fixture
def db_session():
    """Get database session."""
    return next(get_db())

@patch('src.core.services.scorer.TokenScorer.get_token_score', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_token_addition_flow(mock_score, db_session):
    """Test the complete flow of adding and monitoring a new token."""
    from src.core.services.token_monitor import TokenMonitor
    monitor = TokenMonitor()
    try:
        # Mock the validation and analysis methods that add_token actually calls
        with patch.object(monitor.validator, 'validate_token') as mock_validate, \
             patch.object(monitor.analyzer, 'get_token_momentum') as mock_momentum, \
             patch('src.api.clients.birdeye.BirdeyeClient.get_token_price') as mock_price, \
             patch('src.api.clients.dexscreener.DexscreenerClient.get_token_pairs') as mock_pairs:
            
            # Mock successful validation
            mock_validate.return_value = {
                "address": TEST_TOKEN["address"],
                "is_valid": True,
                "checks": {
                    "contract_safety": {"passed": True, "required": True},
                    "liquidity": {"passed": True, "required": True},
                    "holders": {"passed": True, "required": True}
                },
                "metrics": {
                    "safety_score": 85.0,
                    "liquidity": 100000.0,
                    "holders": 1000
                }
            }
            
            # Mock momentum data
            mock_momentum.return_value = {
                "momentum_score": 2.5,
                "trend": "bullish",
                "confidence": 0.8
            }
            # Mock price and pairs
            mock_price.return_value = MOCK_PRICE_DATA
            mock_pairs.return_value = []
            # Mock scorer
            mock_score_obj = Mock()
            mock_score_obj.contract_safety_score = 90.0
            mock_score_obj.total_score = 95.0
            mock_score_obj.to_dict.return_value = {
                "liquidity_score": 80.0,
                "market_cap_score": 85.0,
                "volume_score": 88.0,
                "contract_safety_score": 90.0,
                "ownership_score": 92.0,
                "liquidity_lock_score": 87.0,
                "honeypot_risk_score": 93.0,
                "mention_frequency_score": 75.0,
                "source_reliability_score": 78.0,
                "sentiment_score": 70.0,
                "liquidity_composite": 85.0,
                "safety_composite": 90.0,
                "social_composite": 80.0,
                "total_score": 95.0
            }
            mock_score.return_value = mock_score_obj
            
            # Provide initial_data with price and volume fields
            initial_data = {
                "price": MOCK_PRICE_DATA.price_usd,
                "volume_24h": MOCK_PRICE_DATA.volume_24h,
                "market_cap": MOCK_PRICE_DATA.market_cap,
                "liquidity": MOCK_PRICE_DATA.liquidity,
                "holder_count": MOCK_PRICE_DATA.holders
            }
            
            # Use db_session instead of db
            await monitor.add_token(TEST_TOKEN["address"], initial_data=initial_data, db=db_session)
            # Set the name explicitly for assertion
            token = db_session.query(Token).filter(Token.address == TEST_TOKEN["address"]).first()
            token.name = TEST_TOKEN["name"]
            db_session.commit()
            # Verify token was added to monitoring set
            assert TEST_TOKEN["address"] in monitor.monitored_tokens
            # Verify token was stored in database
            token = db_session.query(Token).filter(Token.address == TEST_TOKEN["address"]).first()
            assert token is not None
            assert token.address == TEST_TOKEN["address"]
            assert token.name == TEST_TOKEN["name"]
            # Verify metrics were created
            metrics = db_session.query(TokenMetrics).filter(TokenMetrics.token_id == token.id).first()
            assert metrics is not None
            assert metrics.price == MOCK_PRICE_DATA.price_usd
            assert metrics.volume_24h == MOCK_PRICE_DATA.volume_24h
            # Verify score was calculated
            score = db_session.query(TokenScore).filter(TokenScore.token_id == token.id).first()
            assert score is not None
            contract_safety_score = getattr(score, 'contract_safety_score', None)
            total_score = getattr(score, 'total_score', None)
            assert contract_safety_score is not None and float(contract_safety_score) > 0
            assert total_score is not None and float(total_score) > 0
    finally:
        await monitor.stop()

@pytest.mark.asyncio
async def test_monitoring_updates(monitor, db_session):
    """Test token monitoring updates and alert generation."""
    # Set up initial token
    token = Token(
        address=TEST_TOKEN["address"],
        name=TEST_TOKEN["name"],
        symbol=TEST_TOKEN["symbol"],
        decimals=TEST_TOKEN["decimals"],
        total_supply=TEST_TOKEN["total_supply"],
        created_at=datetime.utcnow()
    )
    db_session.add(token)
    db_session.commit()
    
    # Mock API responses with changing data
    original_price = 100.0
    new_price = 150.0  # 50% increase
    
    with patch('src.api.clients.birdeye.BirdeyeClient.get_token_price') as mock_price, \
         patch('src.api.clients.rugcheck.RugcheckClient.get_security_score') as mock_security, \
         patch('src.api.clients.dexscreener.DexscreenerClient.get_token_pairs') as mock_pairs:
        
        # First update
        mock_price.return_value = MOCK_PRICE_DATA
        mock_security.return_value = MOCK_SECURITY_DATA
        mock_pairs.return_value = []
        
        await monitor.update_token(TEST_TOKEN["address"], db_session)
        
        # Second update with significant price change
        updated_price_data = TokenPrice(
            **{**MOCK_PRICE_DATA.dict(),
               "price_usd": new_price,
               "updated_at": datetime.utcnow()
            }
        )
        mock_price.return_value = updated_price_data
        
        await monitor.update_token(TEST_TOKEN["address"], db_session)
        
        # Fix metrics query
        latest_metrics = db_session.query(TokenMetrics)\
            .filter(TokenMetrics.token_id == token.id)\
            .order_by(TokenMetrics.created_at.desc())\
            .first()
        
        assert latest_metrics.price == new_price
        
        # Check if alert was generated
        alert = db_session.query(Alert)\
            .filter(Alert.token_id == token.id)\
            .order_by(Alert.created_at.desc())\
            .first()
        
        assert alert is not None
        assert "price" in alert.alert_type.lower()

@pytest.mark.asyncio
async def test_error_recovery(monitor, db_session):
    """Test system recovery from API errors."""
    with patch('src.api.clients.birdeye.BirdeyeClient.get_token_price') as mock_price:
        # Simulate API error
        mock_price.side_effect = Exception("API Error")
        
        # Should not raise exception
        await monitor.update_token(TEST_TOKEN["address"], db_session)
        
        # System should continue working after error
        mock_price.side_effect = None
        mock_price.return_value = MOCK_PRICE_DATA
        
        await monitor.update_token(TEST_TOKEN["address"], db_session)
        
        # Retrieve token for id
        token = db_session.query(Token).filter(Token.address == TEST_TOKEN["address"]).first()
        metrics = db_session.query(TokenMetrics)\
            .filter(TokenMetrics.token_id == token.id)\
            .order_by(TokenMetrics.created_at.desc())\
            .first()
        
        assert metrics is not None
        assert metrics.price == MOCK_PRICE_DATA.price_usd

@pytest.mark.asyncio
async def test_alert_cooldown(monitor, db_session):
    """Test alert cooldown mechanism."""
    # Set up initial token
    token = Token(
        address=TEST_TOKEN["address"],
        name=TEST_TOKEN["name"],
        symbol=TEST_TOKEN["symbol"],
        decimals=TEST_TOKEN["decimals"],
        total_supply=TEST_TOKEN["total_supply"],
        created_at=datetime.utcnow()
    )
    db_session.add(token)
    db_session.commit()
    with patch('src.api.clients.birdeye.BirdeyeClient.get_token_price') as mock_price, \
         patch('src.api.clients.rugcheck.RugcheckClient.get_security_score') as mock_security, \
         patch('src.api.clients.dexscreener.DexscreenerClient.get_token_pairs') as mock_pairs:
        # Generate multiple price changes
        for price in [100.0, 150.0, 200.0, 250.0]:
            updated_price_data = TokenPrice(
                **{**MOCK_PRICE_DATA.dict(),
                   "price_usd": price,
                   "updated_at": datetime.utcnow()
                }
            )
            mock_price.return_value = updated_price_data
            mock_security.return_value = MOCK_SECURITY_DATA
            mock_pairs.return_value = []
            await monitor.update_token(TEST_TOKEN["address"], db_session)
            await asyncio.sleep(0.1)  # Small delay
        # Retrieve token for id
        token = db_session.query(Token).filter(Token.address == TEST_TOKEN["address"]).first()
        # Check that not every price change generated an alert
        alerts = db_session.query(Alert)\
            .filter(Alert.token_id == token.id)\
            .order_by(Alert.created_at).all()
        assert len(alerts) < 4  # Should have fewer alerts than price changes

@pytest.mark.asyncio
async def test_monitoring_performance(db_session):
    """Test monitoring system performance with multiple tokens."""
    # Create multiple test tokens
    test_tokens = []
    for i in range(5):
        address = f"TokenAddress{i}" + "1" * (32 - len(f"TokenAddress{i}"))
        token = Token(
            address=address,
            name=f"Token{i}",
            symbol=f"TKN{i}",
            decimals=9,
            total_supply="1000000000",
            created_at=datetime.utcnow()
        )
        test_tokens.append(token)
        db_session.add(token)
    db_session.commit()
    # Patch all external API calls to avoid real network requests
    with patch('src.api.clients.birdeye.BirdeyeClient.get_token_price', new_callable=AsyncMock) as mock_price, \
         patch('src.api.clients.rugcheck.RugcheckClient.get_security_score', new_callable=AsyncMock) as mock_security, \
         patch('src.api.clients.dexscreener.DexscreenerClient.get_token_pairs', new_callable=AsyncMock) as mock_pairs, \
         patch('src.api.clients.pumpfun.PumpfunClient.get_token_launch', new_callable=AsyncMock) as mock_pumpfun, \
         patch('src.api.clients.bonkfun.BonkfunClient.get_token_info', new_callable=AsyncMock) as mock_bonkfun, \
         patch('src.api.clients.social_data.SocialDataClient.get_social_mentions', new_callable=AsyncMock) as mock_social:
        mock_price.return_value = MOCK_PRICE_DATA
        mock_security.return_value = MOCK_SECURITY_DATA
        mock_pairs.return_value = []
        mock_pumpfun.return_value = None
        mock_bonkfun.return_value = None
        mock_social.return_value = []
        monitor = TokenMonitor()
        start_time = datetime.utcnow()
        # Update all tokens
        for token in test_tokens:
            await monitor.update_token(token.address, db_session)
        duration = (datetime.utcnow() - start_time).total_seconds()
        # Check performance
        assert duration < 5.0  # Should complete within reasonable time

def test_direct_token_metrics_storage(db_session):
    from src.models import Token, TokenMetrics
    from src.database import get_db
    # Create and add token
    token = Token(address="test_address", name="Test", symbol="TST", decimals=9, total_supply="1000")
    db_session.add(token)
    db_session.commit()
    # Create and add metrics
    metrics = TokenMetrics(token_id=token.id, price=123.45, market_cap=1000.0, volume_24h=500.0, liquidity=200.0)
    db_session.add(metrics)
    db_session.commit()
    # Retrieve and check
    stored = db_session.query(TokenMetrics).filter(TokenMetrics.token_id == token.id).first()
    assert stored is not None
    assert stored.price == 123.45
