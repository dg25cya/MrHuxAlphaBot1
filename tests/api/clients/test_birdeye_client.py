"""Tests for the Birdeye API client."""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.api.clients.birdeye import BirdeyeClient, TokenPrice

# Test data
TEST_TOKEN_ADDRESS = "So11111111111111111111111111111111111111112"  # SOL
MOCK_PRICE_RESPONSE = {
    "data": {
        "value": 100.0,
        "valueSol": 1.0,
        "volume24h": 1000000.0,
        "liquidity": 5000000.0,
        "marketCap": 10000000.0,
        "priceChange24h": 5.0,
        "fdMarketCap": 12000000.0,
        "holders": 1000
    }
}

MOCK_METADATA_RESPONSE = {
    "data": {
        "name": "Solana",
        "symbol": "SOL",
        "decimals": 9,
        "totalSupply": "1000000000"
    }
}

MOCK_POOLS_RESPONSE = {
    "data": [
        {
            "poolAddress": "pool123",
            "dex": "Orca",
            "liquidity": 1000000.0,
            "volume24h": 500000.0
        }
    ]
}

@pytest_asyncio.fixture
async def client():
    """Create a Birdeye client instance."""
    client = BirdeyeClient()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_get_token_price(client):
    """Test token price retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_PRICE_RESPONSE)
        )
        
        price_data = await client.get_token_price(TEST_TOKEN_ADDRESS)
        assert isinstance(price_data, TokenPrice)
        assert price_data.price_usd == 100.0
        assert price_data.liquidity == 5000000.0
        assert price_data.market_cap == 10000000.0

@pytest.mark.asyncio
async def test_get_token_metadata(client):
    """Test token metadata retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_METADATA_RESPONSE)
        )
        
        metadata = await client.get_token_metadata(TEST_TOKEN_ADDRESS)
        assert metadata["data"]["name"] == "Solana"
        assert metadata["data"]["symbol"] == "SOL"
        assert metadata["data"]["decimals"] == 9

@pytest.mark.asyncio
async def test_get_defi_pools(client):
    """Test DeFi pools retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_POOLS_RESPONSE)
        )
        
        pools = await client.get_defi_pools(TEST_TOKEN_ADDRESS)
        assert len(pools) == 1
        assert pools[0]["poolAddress"] == "pool123"
        assert pools[0]["dex"] == "Orca"

@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling scenarios."""
    with patch('httpx.AsyncClient.request') as mock_request:
        # Test rate limit error
        mock_request.return_value = Mock(
            status_code=429,
            raise_for_status=Mock(side_effect=Exception("Rate limit exceeded")),
            text="Rate limit exceeded"
        )
        
        with pytest.raises(Exception):
            await client.get_token_price(TEST_TOKEN_ADDRESS)
        
        # Test invalid token error
        mock_request.return_value = Mock(
            status_code=404,
            raise_for_status=Mock(side_effect=Exception("Token not found")),
            text="Token not found"
        )
        
        with pytest.raises(Exception):
            await client.get_token_metadata("InvalidAddress")

@pytest.mark.asyncio
async def test_cache_behavior(client):
    """Test caching behavior."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_PRICE_RESPONSE)
        )
        
        # First call should hit the API
        price1 = await client.get_token_price(TEST_TOKEN_ADDRESS)
        
        # Second call should use cache
        price2 = await client.get_token_price(TEST_TOKEN_ADDRESS)
        
        # Compare relevant fields (ignore updated_at)
        assert price1.price_usd == price2.price_usd
        assert price1.liquidity == price2.liquidity
        assert price1.market_cap == price2.market_cap
        assert price1.volume_24h == price2.volume_24h
        assert price1.price_change_24h == price2.price_change_24h

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check functionality."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_PRICE_RESPONSE)
        )
        
        assert await client.check_status() is True
        
        # Test failed health check
        mock_request.side_effect = Exception("API error")
        assert await client.check_status() is False
