"""Tests for the Bonk.fun API client."""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.api.clients.bonkfun import BonkfunClient, BonkLaunchData, BonkMetrics

# Test data
TEST_TOKEN_ADDRESS = "So11111111111111111111111111111111111111112"
MOCK_TOKEN_INFO = {
    "data": {
        "name": "Test Token",
        "symbol": "TEST",
        "description": "A test token",
        "totalSupply": "1000000000",
        "circulatingSupply": "800000000",
        "launchPrice": "0.1",
        "currentPrice": "0.15",
        "marketCap": "120000000",
        "launchTime": int(datetime.now().timestamp()),
        "website": "https://test.com",
        "socialLinks": {
            "twitter": "https://twitter.com/test",
            "telegram": "https://t.me/test"
        },
        "teamInfo": {
            "name": "Test Team",
            "experience": "5+ years",
            "verified": True
        },
        "vestingSchedule": {
            "team": "12 months linear",
            "advisors": "6 months linear"
        }
    }
}

MOCK_TOKEN_METRICS = {
    "data": {
        "priceChange1h": 2.5,
        "priceChange24h": 15.0,
        "priceChange7d": 25.0,
        "volume24h": 1000000.0,
        "liquidity24h": 500000.0,
        "holdersCount": 1000,
        "transactions24h": 500,
        "socialSentiment": 75.0,
        "communityScore": 85.0
    }
}

MOCK_MARKET_OVERVIEW = {
    "data": {
        "totalTokens": 1000,
        "activeTokens24h": 500,
        "averageVolume24h": 5000000.0,
        "totalMarketCap": 1000000000.0,
        "topPerformers": [
            {
                "address": "token1" + "1" * 32,
                "name": "Top Token 1",
                "priceChange24h": 50.0
            }
        ]
    }
}

@pytest_asyncio.fixture
async def client():
    """Create a Bonk.fun client instance."""
    client = BonkfunClient()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_get_token_info(client):
    """Test token information retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_TOKEN_INFO)
        )
        
        info = await client.get_token_info(TEST_TOKEN_ADDRESS)
        assert isinstance(info, BonkLaunchData)
        assert info.name == "Test Token"
        assert info.total_supply == 1000000000
        assert info.launch_price == 0.1
        assert info.current_price == 0.15
        assert info.team_info is not None
        assert info.vesting_schedule is not None

@pytest.mark.asyncio
async def test_get_token_metrics(client):
    """Test token metrics retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_TOKEN_METRICS)
        )
        
        metrics = await client.get_token_metrics(TEST_TOKEN_ADDRESS)
        assert isinstance(metrics, BonkMetrics)
        assert metrics.price_change_24h == 15.0
        assert metrics.volume_24h == 1000000.0
        assert metrics.holders_count == 1000
        assert metrics.social_sentiment == 75.0

@pytest.mark.asyncio
async def test_get_market_overview(client):
    """Test market overview retrieval."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_MARKET_OVERVIEW)
        )
        
        overview = await client.get_market_overview()
        assert overview["data"]["totalTokens"] == 1000
        assert overview["data"]["activeTokens24h"] == 500
        assert len(overview["data"]["topPerformers"]) == 1

@pytest.mark.asyncio
async def test_get_trending_tokens(client):
    """Test trending tokens retrieval."""
    mock_trending = {
        "data": [
            {**MOCK_TOKEN_INFO["data"], "address": TEST_TOKEN_ADDRESS},
            {**MOCK_TOKEN_INFO["data"], "name": "Token 2", "symbol": "TKN2", "address": "token2" + "1" * 32}
        ]
    }
    
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=mock_trending)
        )
        
        # Also need to mock get_token_info since it's called for each token
        with patch.object(client, 'get_token_info') as mock_get_info:
            # Create proper BonkLaunchData instances with correct field names
            token1 = BonkLaunchData(
                token_address=TEST_TOKEN_ADDRESS,
                name="Test Token",
                symbol="TEST",
                description="A test token",
                total_supply=1000000000,
                circulating_supply=800000000,
                launch_price=0.1,
                current_price=0.15,
                market_cap=120000000,
                launch_time=datetime.fromtimestamp(int(datetime.now().timestamp())),
                website="https://test.com",
                social_links={"twitter": "https://twitter.com/test", "telegram": "https://t.me/test"},
                team_info={"name": "Test Team", "experience": "5+ years", "verified": True},
                vesting_schedule={"team": "12 months linear", "advisors": "6 months linear"}
            )
            token2 = BonkLaunchData(
                token_address="token2" + "1" * 32,
                name="Token 2",
                symbol="TKN2",
                description="A test token",
                total_supply=1000000000,
                circulating_supply=800000000,
                launch_price=0.1,
                current_price=0.15,
                market_cap=120000000,
                launch_time=datetime.fromtimestamp(int(datetime.now().timestamp())),
                website="https://test.com",
                social_links={"twitter": "https://twitter.com/test", "telegram": "https://t.me/test"},
                team_info={"name": "Test Team", "experience": "5+ years", "verified": True},
                vesting_schedule={"team": "12 months linear", "advisors": "6 months linear"}
            )
            mock_get_info.side_effect = [token1, token2]
            
            tokens = await client.get_trending_tokens()
            assert len(tokens) == 2
            assert tokens[0].name == "Test Token"
            assert tokens[1].name == "Token 2"

@pytest.mark.asyncio
async def test_get_token_social(client):
    """Test token social metrics retrieval."""
    mock_social = {
        "data": {
            "twitterFollowers": 10000,
            "telegramMembers": 5000,
            "discordMembers": 2000,
            "socialEngagement": 85.0,
            "sentimentScore": 75.0,
            "recentMentions": [
                {"platform": "twitter", "count": 1000},
                {"platform": "telegram", "count": 500}
            ]
        }
    }
    
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=mock_social)
        )
        
        social = await client.get_token_social(TEST_TOKEN_ADDRESS)
        assert social["data"]["twitterFollowers"] == 10000
        assert social["data"]["sentimentScore"] == 75.0

@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling scenarios."""
    with patch('httpx.AsyncClient.request') as mock_request:
        # Test API key error
        mock_request.return_value = Mock(
            status_code=401,
            raise_for_status=Mock(side_effect=Exception("Invalid API key")),
            text="Invalid API key"
        )
        
        info = await client.get_token_info(TEST_TOKEN_ADDRESS)
        assert info is None
        
        # Test rate limit error
        mock_request.return_value = Mock(
            status_code=429,
            raise_for_status=Mock(side_effect=Exception("Rate limit exceeded")),
            text="Rate limit exceeded"
        )
        
        metrics = await client.get_token_metrics(TEST_TOKEN_ADDRESS)
        assert metrics is None

@pytest.mark.asyncio
async def test_cache_behavior(client):
    """Test caching behavior."""
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=MOCK_TOKEN_INFO)
        )
        
        # First call should hit the API
        info1 = await client.get_token_info(TEST_TOKEN_ADDRESS)
        
        # Second call should use cache
        info2 = await client.get_token_info(TEST_TOKEN_ADDRESS)
        
        assert info1 == info2
        assert mock_request.call_count == 1

@pytest.mark.asyncio
async def test_data_validation(client):
    """Test data validation and type conversion."""
    invalid_data = {
        "data": {
            "name": "Test Token",
            "symbol": "TEST",
            "totalSupply": "invalid",  # Invalid number
            "currentPrice": "not_a_number",  # Invalid number
            "launchTime": "invalid_time",  # Invalid timestamp
            "marketCap": None
        }
    }
    
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value=invalid_data)
        )
        
        info = await client.get_token_info(TEST_TOKEN_ADDRESS)
        assert info is None  # Should return None when validation fails

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check functionality."""
    with patch.object(client, '_check_health_endpoint') as mock_health:
        # First call: healthy
        mock_health.return_value = None  # No exception means success
        assert await client.check_status() is True

        # Second call: simulate failure
        mock_health.side_effect = Exception("API error")
        assert await client.check_status() is False
