"""Birdeye API client implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from .base import BaseAPIClient, retry_on_error
from .social_data import SocialDataClient
from ...config.settings import get_settings
from ...utils.sentiment import SentimentAnalyzer

settings = get_settings()

class TokenPrice(BaseModel):
    """Token price information."""
    address: str
    price_usd: float
    price_sol: float
    volume_24h: float
    liquidity: float
    market_cap: float
    price_change_24h: float
    fully_diluted_market_cap: float
    holders: Optional[int]
    updated_at: datetime

class TokenHolder(BaseModel):
    """Token holder information."""
    address: str
    balance: str
    share: float
    rank: int

class TokenHolderInfo(BaseModel):
    """Complete token holder information."""
    total_supply: str
    holder_count: int
    holders: List[TokenHolder]

class BirdeyeClient(BaseAPIClient):
    """Client for Birdeye API."""

    def __init__(self) -> None:
        super().__init__(
            name="birdeye",
            base_url="https://public-api.birdeye.so",
            rate_limit_calls=300,  # Adjust based on your API tier
            rate_limit_period=60.0,
            cache_ttl=60  # 1 minute cache for price data
        )
        self.api_key = settings.birdeye_api_key
        self.headers = {"X-API-KEY": self.api_key}
        self.social_client = SocialDataClient()
        self.sentiment_analyzer = SentimentAnalyzer()

    @retry_on_error(max_retries=3)
    async def get_token_price(self, address: str) -> TokenPrice:
        """Get token price and market data."""
        endpoint = f"/v1/token/price"
        cache_key = f"price_{address}"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers=self.headers,
            cache_key=cache_key
        )
        
        data = response.get('data', {})
        return TokenPrice(
            address=address,
            price_usd=float(data.get('value', 0)),
            price_sol=float(data.get('valueSol', 0)),
            volume_24h=float(data.get('volume24h', 0)),
            liquidity=float(data.get('liquidity', 0)),
            market_cap=float(data.get('marketCap', 0)),
            price_change_24h=float(data.get('priceChange24h', 0)),
            fully_diluted_market_cap=float(data.get('fdMarketCap', 0)),
            holders=data.get('holders'),
            updated_at=datetime.utcnow()
        )

    @retry_on_error(max_retries=3)
    async def get_holder_info(self, token_address: str) -> Dict[str, Any]:
        """Get detailed holder information for a token."""
        endpoint = f"/v1/token/holders"
        cache_key = f"holders_{token_address}"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": token_address},
            headers=self.headers,
            cache_key=cache_key
        )

        data = response.get('data', {})
        holders = []

        for holder in data.get('holders', []):
            holders.append({
                'address': holder.get('address'),
                'balance': str(holder.get('balance', '0')),
                'share': float(holder.get('share', 0)),
                'rank': int(holder.get('rank', 0))
            })

        return {
            'total_supply': str(data.get('total_supply', '0')),
            'holder_count': int(data.get('holder_count', 0)),
            'holders': holders
        }

    @retry_on_error(max_retries=3)
    async def get_token_transactions(self, token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent token transactions."""
        endpoint = f"/v1/token/transactions"
        cache_key = f"txs_{token_address}"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={
                "address": token_address,
                "limit": limit
            },
            headers=self.headers,
            cache_key=cache_key
        )

        txs = []
        for tx in response.get('data', []):
            txs.append({
                'hash': tx.get('signature'),
                'type': tx.get('type'),
                'amount': str(tx.get('amount', '0')),
                'amount_usd': float(tx.get('amountUsd', 0)),
                'timestamp': datetime.fromtimestamp(tx.get('timestamp', 0)),
                'from_address': tx.get('from'),
                'to_address': tx.get('to')
            })

        return txs

    @retry_on_error(max_retries=3)
    async def get_market_activity(self, token_address: str) -> Dict[str, Any]:
        """Get 24h market activity metrics."""
        endpoint = f"/v1/token/market-activity"
        cache_key = f"activity_{token_address}"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": token_address},
            headers=self.headers,
            cache_key=cache_key
        )

        data = response.get('data', {})
        return {
            'buys_24h': int(data.get('buys_24h', 0)),
            'sells_24h': int(data.get('sells_24h', 0)),
            'unique_buyers_24h': int(data.get('unique_buyers_24h', 0)),
            'unique_sellers_24h': int(data.get('unique_sellers_24h', 0)),
            'avg_buy_amount_usd': float(data.get('avg_buy_amount_usd', 0)),
            'avg_sell_amount_usd': float(data.get('avg_sell_amount_usd', 0)),
            'volume_buy_usd': float(data.get('volume_buy_usd', 0)),
            'volume_sell_usd': float(data.get('volume_sell_usd', 0))
        }

    @retry_on_error(max_retries=3)
    async def get_token_metadata(self, address: str) -> Dict[str, Any]:
        """Get token metadata."""
        endpoint = f"/v1/token/meta"
        cache_key = f"meta_{address}"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    @retry_on_error(max_retries=3)
    async def get_defi_pools(self, address: str) -> List[Dict[str, Any]]:
        """Get DeFi pool information for a token."""
        endpoint = f"/v1/pools/address"
        cache_key = f"pools_{address}"
        
        response = await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )
        
        return response.get("data", [])

    @retry_on_error(max_retries=3)
    async def get_previous_volume(self, token_address: str, hours: int = 24) -> float:
        """Get historical volume data."""
        activity = await self.get_market_activity(token_address)
        return float(activity.get('volume_buy_usd', 0)) + float(activity.get('volume_sell_usd', 0))

    @retry_on_error(max_retries=3)
    async def get_previous_holders(self, token_address: str, days: int = 1) -> int:
        """Get historical holder count."""
        holder_info = await self.get_holder_info(token_address)
        return int(holder_info.get('holder_count', 0))

    @retry_on_error(max_retries=3)
    async def get_whale_transactions(self, token_address: str, min_amount: float = 10000.0) -> List[Dict[str, Any]]:
        """Get whale transactions above minimum amount."""
        txs = await self.get_token_transactions(token_address, limit=100)
        return [tx for tx in txs if float(tx.get('amount_usd', 0)) >= min_amount]

    @retry_on_error(max_retries=3)
    async def get_24h_volume(self, token_address: str) -> float:
        """Get 24-hour trading volume."""
        activity = await self.get_market_activity(token_address)
        return float(activity.get('volume_buy_usd', 0)) + float(activity.get('volume_sell_usd', 0))

    @retry_on_error(max_retries=3)
    async def get_social_mentions(self, token_address: str) -> List[Dict[str, Any]]:
        """Get social media mentions."""
        try:
            # Use the dedicated social data client
            mentions = await self.social_client.get_social_mentions(token_address)
            return mentions
        except Exception as e:
            logger.error(f"Error getting social mentions: {e}")
            return []

    @retry_on_error(max_retries=3)
    async def get_social_sentiment(self, token_address: str) -> Dict[str, Any]:
        """Get social sentiment analysis."""
        try:
            # Get mentions from social client
            mentions = await self.social_client.get_social_mentions(token_address)
            
            # Analyze sentiment using our sentiment analyzer
            sentiment_analysis = self.sentiment_analyzer.analyze_mentions(mentions)
            
            return {
                "sentiment_score": sentiment_analysis["overall_sentiment"],
                "positive_percentage": sentiment_analysis["positive_percentage"],
                "negative_percentage": sentiment_analysis["negative_percentage"],
                "neutral_percentage": sentiment_analysis["neutral_percentage"],
                "mention_count": sentiment_analysis["mention_count"],
                "updated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting social sentiment: {e}")
            return {
                "sentiment_score": 0.0,
                "positive_percentage": 0.0,
                "negative_percentage": 0.0, 
                "neutral_percentage": 0.0,
                "mention_count": 0,
                "updated_at": datetime.utcnow().isoformat()
            }

    async def _check_health_endpoint(self):
        """Check API health by attempting to get SOL price."""
        # Using SOL token address as a health check
        sol_address = "So11111111111111111111111111111111111111112"
        await self.get_token_price(sol_address)

    async def check_status(self) -> bool:
        """Check if the Birdeye API is working properly."""
        try:
            # Use a simple endpoint that doesn't have retry decorator
            sol_address = "So11111111111111111111111111111111111111112"
            endpoint = f"/v1/token/price"
            
            await self._make_request(
                method="GET",
                endpoint=endpoint,
                params={"address": sol_address},
                headers=self.headers
            )
            return True
        except Exception as e:
            logger.error(f"Birdeye API status check failed: {e}")
            return False

    @retry_on_error(max_retries=3)
    async def get_token_holders(self, token_address: str) -> Dict[str, Any]:
        """Get token holder information with detailed analytics."""
        holder_info = await self.get_holder_info(token_address)
        
        # Add additional analytics about holders
        total_holders = holder_info.get('holder_count', 0)
        holders = holder_info.get('holders', [])
        
        # Calculate the percentage held by top holders
        top_10_holders = holders[:10] if len(holders) >= 10 else holders
        top_10_percentage = sum(float(holder.get('share', 0)) for holder in top_10_holders)
        
        # Check for whale concentration
        whale_threshold = 0.05  # 5% ownership
        whales = [h for h in holders if float(h.get('share', 0)) >= whale_threshold]
        whale_count = len(whales)
        whale_percentage = sum(float(holder.get('share', 0)) for holder in whales)
        
        return {
            'total_holders': total_holders,
            'top_10_percentage': top_10_percentage,
            'whale_count': whale_count,
            'whale_percentage': whale_percentage,
            'holder_distribution': {
                'large': len([h for h in holders if float(h.get('share', 0)) >= 0.01]),  # >1%
                'medium': len([h for h in holders if 0.001 <= float(h.get('share', 0)) < 0.01]),  # 0.1-1%
                'small': len([h for h in holders if float(h.get('share', 0)) < 0.001])  # <0.1%
            },
            'raw_holders': holders[:100]  # Limit to first 100 holders
        }

    @retry_on_error(max_retries=3)
    async def get_token_data(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive token data from Birdeye API."""
        try:
            price_url = f"/v1/token/price/{token_address}"
            trades_url = f"/v1/token/trades/{token_address}"

            # Get price data
            price_data = await self._get(price_url)
            trades_data = await self._get(trades_url)

            # Process price data
            data = {
                "price": float(price_data.get("value", {}).get("price", 0)),
                "volume_24h": float(price_data.get("value", {}).get("volume24h", 0)),
                "volume_24h_previous": float(price_data.get("value", {}).get("volume24hPrevious", 0)),
                "price_change_24h": float(price_data.get("value", {}).get("priceChange24h", 0)),
                "price_change_1h": float(price_data.get("value", {}).get("priceChange1h", 0)),
                "market_cap": float(price_data.get("value", {}).get("marketCap", 0)),
                "trades_24h": len(trades_data.get("data", [])),
                "buy_count_24h": sum(1 for t in trades_data.get("data", []) if t.get("side") == "buy")
            }

            return data
        except Exception as e:
            logger.error(f"Error getting token data from Birdeye for {token_address}: {str(e)}")
            return {}
