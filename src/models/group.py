"""Monitored groups model definition."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.utils import get_utc_now
from src.utils.dialect import get_json_type


class MonitoredGroup(Base):
    """Model for storing monitored Telegram groups."""

    __tablename__ = "monitored_groups"

    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100))
    is_active = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)
    added_at = Column(DateTime(timezone=True), default=get_utc_now)
    last_processed_message_id = Column(BigInteger)
    meta_data = Column(get_json_type())

    # Relationships
    mentions = relationship("TokenMention", back_populates="group")

    def __repr__(self) -> None:
        """String representation."""
        return f"<MonitoredGroup {self.name} ({self.group_id})>"
