"""Monitored sources model definition."""
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import json

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    Integer,
    String,
    JSON,
    Text,
    Index,
    ForeignKey
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base
from src.utils import get_utc_now
from src.utils.dialect import get_json_type


class SourceType(str, Enum):
    """Types of monitored sources."""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    X = "x"  # Twitter/X
    WEBSITE = "website"  # Monitor websites for token mentions
    DEX = "dex"  # Monitor DEX pairs/pools
    GITHUB = "github"  # Monitor Github repos for contract changes
    RSS = "rss"  # Free RSS feeds
    REDDIT = "reddit"  # Reddit API is free
    BONK = "bonk"  # Monitor Bonk chain activity and contracts


class OutputType(str, Enum):
    """Types of output channels."""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    X = "x"  # Twitter/X
    WEBHOOK = "webhook"  # Generic webhook support


class AlertPriority(Enum):
    """Priority level for alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TokenTrendType(str, Enum):
    """Types of token trends to monitor."""
    PRICE = "price"
    VOLUME = "volume"
    HOLDERS = "holders"
    MENTIONS = "mentions"
    SENTIMENT = "sentiment"
    SOCIAL = "social"
    GITHUB = "github"


class MonitoredSource(Base):
    """Model for storing monitored sources (Telegram, Discord, X)."""

    __tablename__ = "monitored_sources"

    # Core fields
    id = Column(Integer, primary_key=True)
    type = Column(SQLEnum(SourceType), nullable=False)
    identifier = Column(String, nullable=False)  # Can be group ID, server ID, or X handle
    name = Column(String(100))
    is_active = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)
    added_at = Column(DateTime(timezone=True), default=get_utc_now)
    last_processed_id = Column(String)  # Message ID or tweet ID
    last_scanned_at = Column(DateTime(timezone=True))
    error_count = Column(Integer, default=0)
    meta_data = Column(get_json_type())

    # Monitoring settings
    scan_interval = Column(Integer, default=60)  # Seconds between scans
    priority = Column(SQLEnum(AlertPriority), default=AlertPriority.MEDIUM)
    custom_filters = Column(JSON)  # JSON for flexible filtering options
    
    # Token trend monitoring
    monitored_trends = Column(JSON)  # List of TokenTrendType to monitor
    trend_thresholds = Column(JSON)  # Thresholds for each trend type
    
    # Notification settings
    notification_channels = Column(JSON)  # List of output channel IDs
    alert_template = Column(String)  # Custom alert template
    silence_hours = Column(JSON)  # Hours when notifications are silenced
    rate_limit = Column(Integer)  # Max alerts per hour
    
    # AI settings
    sentiment_analysis = Column(Boolean, default=True)  # Enable sentiment analysis
    pattern_learning = Column(Boolean, default=True)  # Learn from false positives
    smart_filtering = Column(Boolean, default=True)  # Use AI to filter spam

    # Relationships
    # alerts = relationship("Alert", back_populates="source")
    # mentions = relationship("TokenMention", back_populates="source")
    # output_channels = relationship("OutputChannel", secondary="source_channels")

    # Indices
    __table_args__ = (
        Index("idx_monitored_sources_type", "type"),
        Index("idx_monitored_sources_active", "is_active"),
        Index("idx_monitored_sources_identifier", "identifier"),
        Index("idx_monitored_sources_priority", "priority")
    )

    @validates('scan_interval')
    def validate_scan_interval(self, key: str, value: int) -> int:
        """Validate scan interval is reasonable."""
        if value < 10:  # Minimum 10 seconds
            raise ValueError("Scan interval must be at least 10 seconds")
        if value > 86400:  # Maximum 24 hours
            raise ValueError("Scan interval cannot exceed 24 hours")
        return value

    @validates('weight')
    def validate_weight(self, key: str, value: float) -> float:
        """Validate source weight."""
        if not 0 <= value <= 10:
            raise ValueError("Weight must be between 0 and 10")
        return value

    @validates('custom_filters', 'trend_thresholds', 'silence_hours')
    def validate_json(self, key: str, value: Any) -> Dict:
        """Validate JSON fields."""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in {key}")
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be a dictionary")
        return value

    @validates('notification_channels')
    def validate_channels(self, key: str, value: Any) -> List[int]:
        """Validate notification channels."""
        if value is None:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in notification_channels")
        if not isinstance(value, list):
            raise ValueError("notification_channels must be a list")
        return [int(channel_id) for channel_id in value]

    @hybrid_property
    def active_trends(self) -> Set[TokenTrendType]:
        """Get set of active trend types."""
        if not self.monitored_trends:
            return set()
        return {TokenTrendType[trend] for trend in self.monitored_trends 
                if trend in TokenTrendType.__members__}

    def should_scan(self) -> bool:
        """Check if source should be scanned based on last scan time."""
        if not self.is_active:
            return False
        if not self.last_scanned_at:
            return True
        now = get_utc_now()
        return (now - self.last_scanned_at).total_seconds() >= self.scan_interval

    def increment_errors(self) -> None:
        """Increment error count and deactivate if too many errors."""
        self.error_count += 1
        if self.error_count >= 10:  # Deactivate after 10 errors
            self.is_active = False

    def reset_errors(self) -> None:
        """Reset error count after successful scan."""
        self.error_count = 0

    def __repr__(self) -> None:
        """String representation."""
        return f"<MonitoredSource {self.type}:{self.identifier} ({self.name})>"


class OutputChannel(Base):
    """Model for output channels where bot will forward messages."""

    __tablename__ = "output_channels"

    id = Column(Integer, primary_key=True)
    type = Column(SQLEnum(OutputType), nullable=False)
    identifier = Column(String, nullable=False)  # channel_id, webhook_url, or api_key
    name = Column(String)  # channel/webhook name
    added_at = Column(DateTime(timezone=True), default=get_utc_now)
    is_active = Column(Boolean, default=True)
    
    # Message type filters
    is_announcements = Column(Boolean, default=False)
    is_alerts = Column(Boolean, default=True)
    is_stats = Column(Boolean, default=False)
    
    # Customization
    custom_format = Column(Text)  # Custom message format
    emoji_style = Column(String, default="default")  # Emoji style preference
    include_stats = Column(Boolean, default=True)  # Include stats in alerts
    include_links = Column(Boolean, default=True)  # Include source links
    
    # Rate limiting (free tier protection)
    messages_per_minute = Column(Integer, default=20)
    message_count = Column(Integer, default=0)
    last_message = Column(DateTime)
    
    # Error handling
    error_count = Column(Integer, default=0)
    last_error = Column(String)
    last_sent = Column(DateTime)
    
    # New: Analytics
    total_sent = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    average_latency = Column(Float)  # Average sending latency
    
    # New: Channel-specific settings
    channel_settings = Column(JSON)  # Flexible settings per channel type
    backup_channels = Column(JSON)  # Failover channels
    forward_to = Column(JSON)  # Additional forwarding rules

    def __repr__(self) -> None:
        """String representation."""
        return f"<OutputChannel {self.type}:{self.name} ({self.identifier})>"

    class Config:
        """Pydantic config."""
        use_enum_values = True
