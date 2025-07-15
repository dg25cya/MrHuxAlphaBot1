"""Token metrics model definition."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Float,
    Boolean,
    UniqueConstraint,
    Index,
    event
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base
from src.utils import get_utc_now, get_json_type


class TokenMetrics(Base):
    """Token metrics model for storing token performance data."""

    __tablename__ = "token_metrics"

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    
    # Market data
    price = Column(Float)  # Current price in USD
    market_cap = Column(Float)  # Market cap in USD
    volume_24h = Column(Float)  # 24h volume in USD
    liquidity = Column(Float)  # Liquidity in USD
    holder_count = Column(Integer)  # Number of holders
    buy_count_24h = Column(Integer)  # Number of buys in 24h
    sell_count_24h = Column(Integer)  # Number of sells in 24h
    price_change_24h = Column(Float)  # 24h price change percentage

    # Contract metrics
    contract_audit_score = Column(Float)  # Contract security score (0-100)
    is_mint_disabled = Column(Boolean, default=False)  # Whether mint is disabled
    is_lp_locked = Column(Boolean, default=False)  # Whether LP is locked
    lp_lock_time = Column(Integer)  # LP lock time in days
    buy_tax = Column(Float)  # Buy tax percentage
    sell_tax = Column(Float)  # Sell tax percentage

    # Social metrics
    mention_count_24h = Column(Integer)  # Number of social mentions in 24h
    sentiment_score = Column(Float)  # Average sentiment score (-1 to 1)
    engagement_score = Column(Float)  # Social engagement score (0-100)

    # Extended data
    meta_data = Column(get_json_type())  # Additional metrics data

    # Relationships
    token = relationship("Token", back_populates="metrics")
    # alerts = relationship("Alert", back_populates="metrics")

    # Indices and constraints
    __table_args__ = (
        UniqueConstraint("token_id", "created_at", name="uq_token_metrics_timestamp"),
        Index("idx_token_metrics_token_date", "token_id", "created_at"),
        Index("idx_token_metrics_price", "price"),
        Index("idx_token_metrics_market_cap", "market_cap"),
        Index("idx_token_metrics_volume", "volume_24h")
    )

    @validates('contract_audit_score', 'sentiment_score')
    def validate_score(self, key: str, value: float) -> float:
        """Validate score values are within expected ranges."""
        if value is not None:
            if key == 'contract_audit_score' and not (0 <= value <= 100):
                raise ValueError("Contract audit score must be between 0 and 100")
            if key == 'sentiment_score' and not (-1 <= value <= 1):
                raise ValueError("Sentiment score must be between -1 and 1")
        return value

    @validates('price', 'market_cap', 'volume_24h', 'liquidity')
    def validate_numeric(self, key: str, value: Decimal) -> Decimal:
        """Validate numeric values are non-negative."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    def __repr__(self) -> None:
        """String representation."""
        return f"<TokenMetrics token_id={self.token_id} price={self.price} time={self.created_at}>"

# Event listeners
@event.listens_for(TokenMetrics, 'before_insert')
def set_defaults(mapper, connection, target) -> None:
    """Set default values before insert."""
    if target.created_at is None:
        target.created_at = get_utc_now()
