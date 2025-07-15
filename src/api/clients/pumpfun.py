"""Pump.fun API client for token launch data."""
from typing import Dict, Optional, List, Any
from datetime import datetime

from loguru import logger
from pydantic import BaseModel

from ...config.settings import get_settings
from .base import BaseAPIClient, retry_on_error

settings = get_settings()

class TokenLaunchData(BaseModel):
    """Token launch data from Pump.fun."""
    token_address: str
    name: str
    symbol: str
    total_raised: float
    participants: int
    status: str  # 'upcoming', 'active', 'completed'
    start_time: datetime
    end_time: Optional[datetime]
    website: Optional[str]
    socials: Dict[str, str]

class PumpfunClient(BaseAPIClient):
    """Client for Pump.fun API."""

    def __init__(self) -> None:
        super().__init__(
            name="pumpfun",
            base_url="https://api.pump.fun/v1",
            rate_limit_calls=150,
            rate_limit_period=60.0,
            cache_ttl=180  # 3 minutes cache for launch data
        )
        self.api_key = settings.pumpfun_api_key

    @retry_on_error(max_retries=3)
    async def get_token_launch(self, address: str) -> Optional[TokenLaunchData]:
        """Get launch data for a specific token."""
        endpoint = "/token/info"
        cache_key = f"launch_{address}"
        
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
            return TokenLaunchData(
                token_address=address,
                name=data["name"],
                symbol=data["symbol"],
                total_raised=float(data.get("totalRaised", 0)),
                participants=int(data.get("participants", 0)),
                status=data.get("status", "unknown"),
                start_time=datetime.fromtimestamp(data["startTime"]),
                end_time=datetime.fromtimestamp(data["endTime"]) if data.get("endTime") else None,
                website=data.get("website"),
                socials=data.get("socials", {})
            )
        except Exception as e:
            logger.error(f"Failed to get launch data for {address}: {str(e)}")
            return None

    @retry_on_error(max_retries=3)
    async def get_active_launches(self) -> List[TokenLaunchData]:
        """Get all active token launches."""
        endpoint = "/launches/active"
        cache_key = "active_launches"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )
        
        launches = []
        for item in response.get("data", []):
            launches.append(TokenLaunchData(
                token_address=item["tokenAddress"],
                name=item["name"],
                symbol=item["symbol"],
                total_raised=float(item.get("totalRaised", 0)),
                participants=int(item.get("participants", 0)),
                status=item.get("status", "active"),
                start_time=datetime.fromtimestamp(item["startTime"]),
                end_time=datetime.fromtimestamp(item["endTime"]) if item.get("endTime") else None,
                website=item.get("website"),
                socials=item.get("socials", {})
            ))
        return launches

    @retry_on_error(max_retries=3)
    async def get_upcoming_launches(self) -> List[TokenLaunchData]:
        """Get upcoming token launches."""
        endpoint = "/launches/upcoming"
        cache_key = "upcoming_launches"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )
        
        launches = []
        for item in response.get("data", []):
            launches.append(TokenLaunchData(
                token_address=item["tokenAddress"],
                name=item["name"],
                symbol=item["symbol"],
                total_raised=float(item.get("totalRaised", 0)),
                participants=int(item.get("participants", 0)),
                status="upcoming",
                start_time=datetime.fromtimestamp(item["startTime"]),
                end_time=datetime.fromtimestamp(item["endTime"]) if item.get("endTime") else None,
                website=item.get("website"),
                socials=item.get("socials", {})
            ))
        return launches

    @retry_on_error(max_retries=3)
    async def get_launch_stats(self, address: str) -> Dict[str, Any]:
        """Get detailed statistics for a token launch."""
        endpoint = f"/launch/stats"
        cache_key = f"stats_{address}"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    async def _check_health_endpoint(self):
        """Check API health by fetching active launches."""
        launches = await self.get_active_launches()
        if launches is None:
            raise Exception("Failed to fetch active launches")

    async def check_status(self) -> bool:
        """Check if the Pump.fun API is working properly."""
        try:
            await self._check_health_endpoint()
            return True
        except Exception as e:
            logger.error(f"Pump.fun API status check failed: {e}")
            return False
