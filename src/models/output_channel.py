"""Output channel model definition."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    JSON,
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship, validates

from src.models.base import Base
from src.utils import get_utc_now
from src.utils.dialect import get_json_type
from src.models.monitored_source import OutputType

class OutputChannel(Base):
    """Output channel model."""
    __tablename__ = 'output_channels'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    identifier = Column(String(255), nullable=False)
    name = Column(String(255))
    added_at = Column(DateTime, default=get_utc_now)
    is_active = Column(Boolean, default=True)
    
    # Channel capabilities
    is_announcements = Column(Boolean, default=True)
    is_alerts = Column(Boolean, default=True)
    is_stats = Column(Boolean, default=True)
    
    # Channel settings
    custom_format = Column(Text)
    emoji_style = Column(String(50))
    include_stats = Column(Boolean, default=True)
    include_links = Column(Boolean, default=True)
    messages_per_minute = Column(Integer, default=30)
    
    # Message tracking
    message_count = Column(BigInteger, default=0)
    last_message = Column(DateTime)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Performance metrics
    last_sent = Column(DateTime)
    total_sent = Column(BigInteger, default=0)
    total_failed = Column(Integer, default=0)
    average_latency = Column(Float, default=0.0)
    
    # Channel configuration
    channel_settings = Column(get_json_type(), default=dict)
    backup_channels = Column(get_json_type(), default=list)
    forward_to = Column(get_json_type(), default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    def __repr__(self) -> None:
        """String representation."""
        return f"<OutputChannel {self.name} ({self.type})>"

    @validates('type')
    def validate_type(self, key, value) -> None:
        """Validate type is a valid OutputType."""
        if not isinstance(value, OutputType) and value not in [e.value for e in OutputType]:
            raise ValueError(f"Invalid output type: {value}")
        return value if isinstance(value, str) else value.value