"""Token model definition."""
from typing import Optional, Dict, Any

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base
from src.utils import get_utc_now
from src.utils.dialect import get_json_type


class Token(Base):
    """Token model for storing Solana token information."""

    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    address = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), index=True)
    symbol = Column(String(20), index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    first_seen_at = Column(DateTime)
    last_updated_at = Column(DateTime)
    mint_authority = Column(String(64))
    total_supply = Column(Numeric(20, 0))
    decimals = Column(Integer)
    is_mint_disabled = Column(Boolean)
    is_blacklisted = Column(Boolean, default=False)
    meta_data = Column(get_json_type())

    # Relationships
    metrics = relationship("TokenMetrics", back_populates="token", lazy="dynamic")
    mentions = relationship("TokenMention", back_populates="token", lazy="dynamic")
    alerts = relationship("Alert", back_populates="token", lazy="select")

    # Indices
    __table_args__ = (
        Index("idx_token_symbol_address", "symbol", "address"),
        Index("idx_token_created_at", "created_at"),
        Index("idx_token_blacklisted", "is_blacklisted")
    )

    @hybrid_property
    def current_price(self) -> Optional[float]:
        """Get current token price."""
        latest_metrics = self.metrics.order_by(TokenMetrics.created_at.desc()).first()
        return float(latest_metrics.price) if latest_metrics and latest_metrics.price else None

    @hybrid_property
    def market_cap(self) -> Optional[float]:
        """Get current market cap."""
        latest_metrics = self.metrics.order_by(TokenMetrics.created_at.desc()).first()
        return float(latest_metrics.market_cap) if latest_metrics and latest_metrics.market_cap else None

    def update_metadata(self, data: Dict[str, Any]) -> None:
        """Update token metadata."""
        if not isinstance(data, dict):
            raise ValueError("Metadata must be a dictionary")
        self.meta_data = {**(self.meta_data or {}), **data}
        self.last_updated_at = get_utc_now()

    def validate(self) -> bool:
        """Validate token data."""
        if not self.address or len(self.address) != 64:
            return False
        if not self.symbol or len(self.symbol) > 20:
            return False
        if self.name and len(self.name) > 100:
            return False
        return True

    def __repr__(self) -> None:
        """String representation."""
        return f"<Token {self.symbol} ({self.address})>"
