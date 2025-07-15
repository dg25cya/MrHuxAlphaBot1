"""Bonk.fun API client for token launch data."""
from typing import Dict, Optional, List, Any
from datetime import datetime

from loguru import logger
from pydantic import BaseModel

from ...config.settings import get_settings
from .base import BaseAPIClient, retry_on_error

settings = get_settings()

class BonkLaunchData(BaseModel):
    """Token launch data from Bonk.fun."""
    token_address: str
    name: str
    symbol: str
    description: str
    total_supply: int
    circulating_supply: int
    launch_price: float
    current_price: float
    market_cap: float
    launch_time: datetime
    website: Optional[str]
    social_links: Dict[str, str]
    team_info: Optional[Dict[str, Any]]
    vesting_schedule: Optional[Dict[str, Any]]

class BonkMetrics(BaseModel):
    """Token metrics from Bonk.fun."""
    price_change_1h: float
    price_change_24h: float
    price_change_7d: float
    volume_24h: float
    liquidity_24h: float
    holders_count: int
    transactions_24h: int
    social_sentiment: Optional[float]
    community_score: Optional[float]

class BonkfunClient(BaseAPIClient):
    """Client for Bonk.fun API."""

    def __init__(self) -> None:
        super().__init__(
            name="bonkfun",
            base_url="https://api.bonk.fun/v1",
            rate_limit_calls=200,
            rate_limit_period=60.0,
            cache_ttl=120  # 2 minutes cache for token data
        )
        self.api_key = settings.bonkfun_api_key

    @retry_on_error(max_retries=3)
    async def get_token_info(self, address: str) -> Optional[BonkLaunchData]:
        """Get comprehensive token information."""
        endpoint = "/token/info"
        cache_key = f"info_{address}"
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint=endpoint,
                params={"address": address},
                headers={"X-API-KEY": self.api_key},
                cache_key=cache_key
            )
            
            if not response.get("data"):
                return None
                
            data = response["data"]
            return BonkLaunchData(
                token_address=address,
                name=data["name"],
                symbol=data["symbol"],
                description=data.get("description", ""),
                total_supply=int(data["totalSupply"]),
                circulating_supply=int(data.get("circulatingSupply", 0)),
                launch_price=float(data.get("launchPrice", 0)),
                current_price=float(data.get("currentPrice", 0)),
                market_cap=float(data.get("marketCap", 0)),
                launch_time=datetime.fromtimestamp(data["launchTime"]),
                website=data.get("website"),
                social_links=data.get("socialLinks", {}),
                team_info=data.get("teamInfo"),
                vesting_schedule=data.get("vestingSchedule")
            )
        except Exception as e:
            logger.error(f"Failed to get token info for {address}: {str(e)}")
            return None

    @retry_on_error(max_retries=3)
    async def get_token_metrics(self, address: str) -> Optional[BonkMetrics]:
        """Get token performance metrics."""
        endpoint = "/token/metrics"
        cache_key = f"metrics_{address}"
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint=endpoint,
                params={"address": address},
                headers={"X-API-KEY": self.api_key},
                cache_key=cache_key
            )
            
            if not response.get("data"):
                return None
                
            data = response["data"]
            return BonkMetrics(
                price_change_1h=float(data.get("priceChange1h", 0)),
                price_change_24h=float(data.get("priceChange24h", 0)),
                price_change_7d=float(data.get("priceChange7d", 0)),
                volume_24h=float(data.get("volume24h", 0)),
                liquidity_24h=float(data.get("liquidity24h", 0)),
                holders_count=int(data.get("holdersCount", 0)),
                transactions_24h=int(data.get("transactions24h", 0)),
                social_sentiment=data.get("socialSentiment"),
                community_score=data.get("communityScore")
            )
        except Exception as e:
            logger.error(f"Failed to get token metrics for {address}: {str(e)}")
            return None

    @retry_on_error(max_retries=3)
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview with trending tokens."""
        endpoint = "/market/overview"
        cache_key = "market_overview"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    @retry_on_error(max_retries=3)
    async def get_trending_tokens(self) -> List[BonkLaunchData]:
        """Get list of trending tokens."""
        endpoint = "/market/trending"
        cache_key = "trending_tokens"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )
        
        tokens = []
        for item in response.get("data", []):
            token = await self.get_token_info(item["address"])
            if token:
                tokens.append(token)
        
        return tokens

    @retry_on_error(max_retries=3)
    async def get_token_social(self, address: str) -> Dict[str, Any]:
        """Get token social metrics and community data."""
        endpoint = "/token/social"
        cache_key = f"social_{address}"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    async def _check_health_endpoint(self):
        """Check API health by fetching market overview."""
        overview = await self.get_market_overview()
        if not overview:
            raise Exception("Failed to fetch market overview")

    async def check_status(self) -> bool:
        """Check if the Bonk.fun API is working properly."""
        try:
            await self._check_health_endpoint()
            return True
        except Exception as e:
            logger.error(f"Bonk.fun API status check failed: {e}")
            return False
