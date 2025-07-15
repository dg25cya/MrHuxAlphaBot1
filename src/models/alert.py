"""Alert model definition."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.utils import get_utc_now, get_json_type


class AlertType(str, Enum):
    """Types of alerts that can be generated."""
    PRICE = "price"  # Price movement alerts
    VOLUME = "volume"  # Volume change alerts
    HOLDERS = "holders"  # Holder count change alerts
    MINT = "mint"  # Mint activity alerts
    TRADE = "trade"  # Large trade alerts
    SOCIAL = "social"  # Social media activity alerts
    CONTRACT = "contract"  # Contract change alerts
    LIQUIDITY = "liquidity"  # Liquidity change alerts
    SECURITY = "security"  # Security risk alerts
    CUSTOM = "custom"  # Custom alerts


class AlertPriority(str, Enum):
    """Priority levels for alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    """Model for storing token alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)  # e.g., "price_increase", "new_listing"
    priority = Column(SQLEnum(AlertPriority), nullable=False, default=AlertPriority.MEDIUM)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    token = relationship("Token", back_populates="alerts")
    # metrics = relationship("TokenMetrics", back_populates="alerts", uselist=False)

    def __repr__(self) -> None:
        """String representation."""
        return f"<Alert(id={self.id}, token_id={self.token_id}, type={self.alert_type})>"

    @property
    def is_stale(self) -> bool:
        """Check if alert is too old to process."""
        if not self.created_at:
            return True
        return (datetime.utcnow() - self.created_at).total_seconds() > 3600  # 1 hour

    def mark_delivered(self) -> None:
        """Mark alert as delivered."""
        self.delivered = True
        self.processed_at = get_utc_now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "token_symbol": self.token_symbol,
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "price": self.price,
            "market_cap": self.market_cap,
            "volume_24h": self.volume_24h,
            "metadata": self.metadata or {}
        }
