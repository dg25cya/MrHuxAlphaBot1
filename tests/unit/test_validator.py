"""Tests for token validation service."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.schemas.token_data import TokenMarketData
from src.schemas.token_safety import TokenSafetyData
from src.api.clients.pumpfun import TokenLaunchData
from src.api.clients.bonkfun import BonkLaunchData
from src.core.services.validator import TokenValidator, TokenValidationResult
from src.utils import get_utc_now


@pytest.fixture
def mock_market_data():
    """Create mock market data."""
    return TokenMarketData(
        price=1.5,
        price_usd=1.5,
        volume_24h=50_000,
        liquidity=1_000_000,
        liquidity_usd=1_000_000,
        price_change_24h=5.0,
        created_at=get_utc_now(),
        verified=True,
        pair_address="pair123"
    )


@pytest.fixture
def mock_safety_data():
    """Create mock safety data."""
    return TokenSafetyData(
        mint_authority=None,
        is_mint_disabled=True,
        total_supply=1_000_000_000,
        decimals=9,
        holders_count=1000,
        is_verified=True,
        lp_locked=True,
        is_honeypot=False,
        buy_tax=5.0,
        sell_tax=5.0,
        risk_level="LOW",
        risk_factors=[],
        created_at=get_utc_now()
    )


@pytest.fixture
def validator(db_session):
    """Create TokenValidator instance with mocked clients."""
    validator = TokenValidator(db_session)
    
    # Create mock clients
    validator.dexscreener = AsyncMock()
    validator.dexscreener.get_token_pairs = AsyncMock()
    
    validator.rugcheck = AsyncMock()
    validator.rugcheck.check_token = AsyncMock()
    
    validator.pumpfun = AsyncMock()
    validator.pumpfun.get_token_info = AsyncMock()
    
    validator.bonkfun = AsyncMock()
    validator.bonkfun.get_token_info = AsyncMock()
    
    return validator


@pytest.mark.asyncio
async def test_validate_token_success(validator, mock_market_data, mock_safety_data):
    """Test successful token validation."""
    # Setup mocks
    validator.dexscreener.get_token_pairs.return_value = mock_market_data
    validator.rugcheck.check_token.return_value = mock_safety_data
    validator.pumpfun.get_token_info.return_value = None
    validator.bonkfun.get_token_info.return_value = None
    
    # Validate token
    address = "So11111111111111111111111111111111111111111"
    result = await validator.validate_token(address=address)
    
    assert result.address == address
    assert not result.is_honeypot
    assert result.verdict == "VALID"
    assert result.risk_level == "LOW"


@pytest.mark.asyncio
async def test_validate_token_honeypot(validator, mock_market_data, mock_safety_data):
    """Test validation of honeypot token."""
    # Setup honeypot mock data
    mock_safety_data.is_honeypot = True
    validator.dexscreener.get_token_pairs.return_value = mock_market_data
    validator.rugcheck.check_token.return_value = mock_safety_data
    validator.pumpfun.get_token_info.return_value = None
    validator.bonkfun.get_token_info.return_value = None
    
    # Validate token
    address = "So11111111111111111111111111111111111111111"
    result = await validator.validate_token(address=address)
    
    assert result.verdict == "INVALID"
    assert result.is_honeypot


@pytest.mark.asyncio
async def test_validate_token_high_tax(validator, mock_market_data, mock_safety_data):
    """Test validation of token with high tax."""
    # Setup high tax mock data
    mock_safety_data.buy_tax = 15
    mock_safety_data.sell_tax = 15
    validator.dexscreener.get_token_pairs.return_value = mock_market_data
    validator.rugcheck.check_token.return_value = mock_safety_data
    validator.pumpfun.get_token_info.return_value = None
    validator.bonkfun.get_token_info.return_value = None
    
    # Validate token
    address = "So11111111111111111111111111111111111111111"
    result = await validator.validate_token(address=address)
    
    assert result.verdict == "INVALID"
    assert result.high_tax


@pytest.mark.asyncio
async def test_validate_token_low_liquidity(validator, mock_market_data, mock_safety_data):
    """Test validation of token with low liquidity."""
    # Setup low liquidity mock data
    mock_market_data.liquidity = 100
    mock_market_data.liquidity_usd = 100
    validator.dexscreener.get_token_pairs.return_value = mock_market_data
    validator.rugcheck.check_token.return_value = mock_safety_data
    validator.pumpfun.get_token_info.return_value = None
    validator.bonkfun.get_token_info.return_value = None
    
    # Validate token
    address = "So11111111111111111111111111111111111111111"
    result = await validator.validate_token(address=address)
    
    assert result.verdict == "INVALID"
    assert result.insufficient_liquidity


@pytest.mark.asyncio
async def test_validate_token_api_failure(validator):
    """Test handling of API failures during validation."""
    # Setup mock failure
    validator.dexscreener.get_token_pairs.side_effect = Exception("API Error")
    
    # Validate token
    address = "So11111111111111111111111111111111111111111"
    result = await validator.validate_token(address=address)
    
    assert result.verdict == "ERROR"
    assert "API Error" in result.error_message
