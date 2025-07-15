"""Notification channel model for managing output destinations."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, BigInteger, Text
from sqlalchemy.sql import func

from src.models.base import Base


class NotificationChannel(Base):
    """Model for managing notification channels where bot alerts are sent."""
    
    __tablename__ = 'notification_channels'

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False, unique=True)  # Telegram channel/group ID
    name = Column(String(100))
    type = Column(String(20), default='telegram')  # telegram, discord, etc.
    
    # Channel status and configuration
    is_active = Column(Boolean, default=True)
    is_alerts = Column(Boolean, default=True)  # Whether to send alert notifications
    is_stats = Column(Boolean, default=True)  # Whether to send periodic stats
    
    # Message formatting
    custom_format = Column(Text)  # Custom message template
    emoji_style = Column(String(20), default='default')  # Emoji style for messages
    include_stats = Column(Boolean, default=True)  # Include token stats in messages
    include_links = Column(Boolean, default=True)  # Include relevant links
    
    # Rate limiting and monitoring
    messages_per_minute = Column(Integer, default=20)
    rate_limit = Column(Integer, default=60)  # Rate limit in seconds
    
    # Channel statistics
    message_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    average_latency = Column(Float, default=0.0)
    
    # Last activity tracking
    last_message = Column(Text)
    last_error = Column(Text)
    last_sent = Column(DateTime(timezone=True))
    
    # Metadata and settings
    channel_settings = Column(JSON)  # Additional channel-specific settings
    backup_channels = Column(JSON)  # Backup channels for failover
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
