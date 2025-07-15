"""Token data models."""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class TokenMarketData(BaseModel):
    """Token market data from DEX aggregators."""
    price_usd: Optional[float] = None
    price_native: Optional[float] = None
    liquidity_usd: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    holders: Optional[int] = None
    transactions_24h: Optional[int] = None
    price_change_24h: Optional[float] = None
    updated_at: datetime
    dex: Optional[str] = None


class TokenSocialData(BaseModel):
    """Token social metrics."""
    mentions_24h: int = 0
    engagement_score: float = 0.0
    sentiment_score: float = 0.0
    unique_addresses_24h: int = 0
    updated_at: datetime
