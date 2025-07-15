"""Token scoring model."""

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.utils.dialect import get_json_type
from src.utils import get_utc_now
from src.utils.datetime_types import TZDateTime


class TokenScore(Base):
    """Model for storing token scoring data."""

    __tablename__ = "token_scores"

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"))
    
    # Always store as UTC
    calculated_at = Column(TZDateTime, default=get_utc_now)
    
    # Liquidity metrics (0-100)
    liquidity_score = Column(Float)
    market_cap_score = Column(Float)
    volume_score = Column(Float)
    
    # Safety metrics (0-100)
    contract_safety_score = Column(Float)
    ownership_score = Column(Float)
    liquidity_lock_score = Column(Float)
    honeypot_risk_score = Column(Float)
    
    # Social metrics (0-100)
    mention_frequency_score = Column(Float)
    source_reliability_score = Column(Float)
    sentiment_score = Column(Float)
    
    # Overall scores
    liquidity_composite = Column(Float)  # Weighted average of liquidity metrics
    safety_composite = Column(Float)    # Weighted average of safety metrics
    social_composite = Column(Float)    # Weighted average of social metrics
    total_score = Column(Float)         # Final weighted score
    
    # Detailed metrics snapshot
    raw_metrics = Column(get_json_type())
    
    # Relationships
    token = relationship("Token", backref="scores")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TokenScore {self.token_id} ({self.total_score})>"
