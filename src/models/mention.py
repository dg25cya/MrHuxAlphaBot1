"""Token mentions model definition."""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.utils import get_utc_now
from src.utils.dialect import get_json_type


class TokenMention(Base):
    """Model for storing token mentions in monitored groups."""

    __tablename__ = "token_mentions"

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"))
    token = relationship("Token", back_populates="mentions")
    
    group_id = Column(Integer, ForeignKey("monitored_groups.id"))
    group = relationship("MonitoredGroup", back_populates="mentions")
    
    message_id = Column(Integer)
    message_text = Column(Text)
    sentiment = Column(Float)  # Sentiment score from -1 to 1
    
    mentioned_at = Column(DateTime(timezone=True), default=get_utc_now)
    meta_data = Column(get_json_type())

    def __repr__(self) -> None:
        """String representation."""
        return f"<TokenMention(token_id={self.token_id}, group_id={self.group_id})>"
