"""Schemas for admin dashboard data."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class TokenMomentumStats(BaseModel):
    """Token momentum statistics."""
    score: float = Field(..., description="Momentum score")
    hype_level: str = Field(..., description="Current hype level")
    mention_count: int = Field(..., description="Number of mentions")
    avg_sentiment: float = Field(..., description="Average sentiment score")

class MetricDataPoint(BaseModel):
    """Single metric data point."""
    timestamp: datetime
    value: float

class TokenMetrics(BaseModel):
    """Token metrics history."""
    price_history: List[MetricDataPoint]
    volume_history: List[MetricDataPoint]

class DashboardStats(BaseModel):
    """Overall dashboard statistics."""
    total_tokens: int = Field(..., description="Total number of tracked tokens")
    new_tokens: int = Field(..., description="New tokens in timeframe")
    total_mentions: int = Field(..., description="Total token mentions")
    avg_sentiment: float = Field(..., description="Average sentiment score")
    high_momentum_tokens: int = Field(..., description="Tokens with high momentum")
    timeframe: str = Field(..., description="Stats timeframe")

class TokenListItem(BaseModel):
    """Token list item with basic analytics."""
    address: str
    created_at: datetime
    momentum_score: float
    mention_count: int
    avg_sentiment: float
    hype_level: str

class TokenListResponse(BaseModel):
    """Response model for token list endpoint."""
    tokens: List[TokenListItem]
    total: int
    limit: int
    offset: int

class TokenDetailResponse(BaseModel):
    """Response model for token details endpoint."""
    address: str
    created_at: datetime
    momentum: TokenMomentumStats
    metrics: TokenMetrics
    timeframe: str

class MomentumDistribution(BaseModel):
    """Distribution of token momentum levels."""
    extreme: int = Field(0, description="Number of tokens with extreme momentum")
    high: int = Field(0, description="Number of tokens with high momentum")
    medium: int = Field(0, description="Number of tokens with medium momentum")
    low: int = Field(0, description="Number of tokens with low momentum")

class SentimentDistribution(BaseModel):
    """Distribution of token sentiment levels."""
    very_positive: int = Field(0, description="Number of very positive mentions")
    positive: int = Field(0, description="Number of positive mentions")
    negative: int = Field(0, description="Number of negative mentions")
    very_negative: int = Field(0, description="Number of negative mentions")

class TokenAnalytics(BaseModel):
    """Overall token analytics."""
    momentum_distribution: MomentumDistribution
    sentiment_distribution: SentimentDistribution
    timeframe: str

class TokenStats(BaseModel):
    """Detailed token statistics."""
    address: str
    name: Optional[str]
    symbol: Optional[str]
    created_at: datetime
    safety_score: Optional[float]
    hype_score: Optional[float]
    is_blacklisted: bool
    blacklist_reason: Optional[str]
    metrics: Dict[str, Any]

    class Config:
        from_attributes = True

class TokenFilter(BaseModel):
    """Token filtering parameters."""
    address: Optional[str] = None
    min_safety_score: Optional[float] = Field(None, ge=0, le=100)
    min_hype_score: Optional[float] = Field(None, ge=0, le=100)
    is_blacklisted: Optional[bool] = None

class SystemHealth(BaseModel):
    """System health metrics."""
    bot_status: str = Field(..., description="Current bot operational status")
    uptime: float = Field(..., description="Bot uptime in seconds")
    api_health: Dict[str, bool] = Field(..., description="Health status of connected APIs")
    telegram_rate_limits: Dict[str, Any] = Field(..., description="Current Telegram rate limit status")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage")
    memory_usage: float = Field(..., ge=0, description="Memory usage in MB")

class BotConfig(BaseModel):
    """Bot configuration settings."""
    min_safety_score: float = Field(..., ge=0, le=100, description="Minimum safety score for alerts")
    min_hype_score: float = Field(..., ge=0, le=100, description="Minimum hype score for alerts")
    alert_cooldown: int = Field(..., ge=300, description="Cooldown period between alerts in seconds")
    max_daily_alerts: int = Field(..., ge=1, description="Maximum number of alerts per day")
    blacklist_threshold: float = Field(..., ge=0, le=100, description="Score threshold for auto-blacklisting")
    monitoring_interval: int = Field(..., ge=60, description="Token monitoring interval in seconds")
    cleanup_interval: int = Field(..., ge=3600, description="Data cleanup interval in seconds")

class TimePoint(BaseModel):
    """Single point in time series data."""
    timestamp: datetime
    value: float

class TimeSeriesData(BaseModel):
    """Time series data for metrics."""
    metric: str
    data: List[TimePoint]
    
class PerformanceMetrics(BaseModel):
    """Detailed performance metrics."""
    token_processing_time: float = Field(..., description="Average token processing time in seconds")
    daily_tokens_parsed: int = Field(..., description="Number of tokens parsed in last 24h")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage")
    successful_alerts: int = Field(..., description="Number of successful alerts")
    failed_alerts: int = Field(..., description="Number of failed alerts")

class MonitoredGroup(BaseModel):
    """Monitored group schema."""
    id: int
    group_id: int
    name: Optional[str] = None
    is_active: bool = True
    weight: float = 1.0
    added_at: datetime
    last_processed_message_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class GroupUpdate(BaseModel):
    """Group update parameters."""
    is_active: Optional[bool] = Field(None, description="Whether group monitoring is active")
    min_mentions: Optional[int] = Field(None, ge=1, description="Minimum mentions for token tracking")
    alert_threshold: Optional[float] = Field(None, ge=0, le=100, description="Alert threshold score")
    cooldown_override: Optional[int] = Field(None, ge=0, description="Group-specific alert cooldown")

class AlertConfig(BaseModel):
    """Alert configuration settings."""
    enabled: bool = True
    min_combined_score: float = Field(60.0, ge=0, le=100)
    cooldown_minutes: int = Field(60, ge=5)
    notification_channels: List[str] = Field(default_factory=list)
    alert_template: str = Field(
        "{symbol} Alert!\n"
        "Safety: {safety_score}/100\n"
        "Hype: {hype_score}/100\n"
        "Price: ${price}\n"
        "24h Volume: ${volume_24h:,.0f}"
    )
