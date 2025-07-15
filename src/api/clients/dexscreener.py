"""Dexscreener API client implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from .base import BaseAPIClient, retry_on_error
from ...config.settings import get_settings

settings = get_settings()

class TokenPair(BaseModel):
    """Token pair information from Dexscreener."""
    pair_address: str
    base_token: str
    quote_token: str
    price_usd: float
    price_native: float
    liquidity_usd: float
    volume_24h: float
    price_change_24h: float
    created_at: datetime
    dex: str
    url: str

class DexscreenerClient(BaseAPIClient):
    """Client for Dexscreener API."""

    def __init__(self) -> None:
        super().__init__(
            name="dexscreener",
            base_url="https://api.dexscreener.com/latest",
            rate_limit_calls=200,
            rate_limit_period=60.0,
            cache_ttl=120  # 2 minutes cache for market data
        )

    @retry_on_error(max_retries=3)
    async def get_token_pairs(self, address: str) -> List[TokenPair]:
        """Get all pairs for a token."""
        endpoint = f"/dex/tokens/{address}"
        cache_key = f"pairs_{address}"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            cache_key=cache_key
        )
        
        pairs = []
        for pair in response.get("pairs", []):
            # Only include Solana pairs
            if pair.get("chainId") != "solana":
                continue
                
            pairs.append(TokenPair(
                pair_address=pair["pairAddress"],
                base_token=pair["baseToken"]["address"],
                quote_token=pair["quoteToken"]["address"],
                price_usd=float(pair.get("priceUsd", 0)),
                price_native=float(pair.get("priceNative", 0)),
                liquidity_usd=float(pair.get("liquidity", {}).get("usd", 0)),
                volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                price_change_24h=float(pair.get("priceChange", {}).get("h24", 0)),
                created_at=datetime.fromtimestamp(pair.get("pairCreatedAt", 0)),
                dex=pair.get("dexId", "unknown"),
                url=pair.get("url", "")
            ))
        
        return pairs

    @retry_on_error(max_retries=3)
    async def search_pairs(self, query: str) -> List[TokenPair]:
        """Search for pairs by token name or symbol."""
        endpoint = f"/dex/search"
        cache_key = f"search_{query}"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"q": query},
            cache_key=cache_key
        )
        
        pairs = []
        for pair in response.get("pairs", []):
            if pair.get("chainId") == "solana":
                pairs.append(TokenPair(
                    pair_address=pair["pairAddress"],
                    base_token=pair["baseToken"]["address"],
                    quote_token=pair["quoteToken"]["address"],
                    price_usd=float(pair.get("priceUsd", 0)),
                    price_native=float(pair.get("priceNative", 0)),
                    liquidity_usd=float(pair.get("liquidity", {}).get("usd", 0)),
                    volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                    price_change_24h=float(pair.get("priceChange", {}).get("h24", 0)),
                    created_at=datetime.fromtimestamp(pair.get("pairCreatedAt", 0)),
                    dex=pair.get("dexId", "unknown"),
                    url=pair.get("url", "")
                ))
        
        return pairs

    @retry_on_error(max_retries=3)
    async def get_token_data(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive token data including pairs, liquidity, and volume.
        
        This is a wrapper around get_token_pairs that formats the data in a way
        expected by the token_validation service.
        """
        pairs = await self.get_token_pairs(token_address)
        
        if not pairs:
            return {
                "address": token_address,
                "liquidity": 0,
                "volume_24h": 0,
                "price": 0,
                "price_change_24h": 0,
                "pairs": []
            }
        
        # Sort pairs by liquidity
        pairs.sort(key=lambda p: p.liquidity_usd, reverse=True)
        top_pair = pairs[0]
        
        # Calculate total liquidity and volume
        total_liquidity = sum(p.liquidity_usd for p in pairs)
        total_volume = sum(p.volume_24h for p in pairs)
        
        return {
            "address": token_address,
            "liquidity": total_liquidity,
            "volume_24h": total_volume,
            "price": top_pair.price_usd,
            "price_change_24h": top_pair.price_change_24h,
            "pairs": [
                {
                    "pair_address": p.pair_address,
                    "dex": p.dex,
                    "liquidity": p.liquidity_usd,
                    "volume_24h": p.volume_24h,
                    "price": p.price_usd,
                    "url": p.url
                }
                for p in pairs
            ]
        }

    async def _check_health_endpoint(self):
        """Check API health by searching for SOL pairs."""
        pairs = await self.search_pairs("SOL")
        if not pairs:
            raise Exception("No SOL pairs found in health check")

    async def check_status(self) -> bool:
        """Check if the API is operational."""
        try:
            await self._check_health_endpoint()
            return True
        except Exception as e:
            logger.error(f"Dexscreener health check failed: {e}")
            return False
