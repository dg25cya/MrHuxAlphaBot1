"""Source to channel mapping table."""
from sqlalchemy import Column, ForeignKey, Integer, Table

from src.models.base import Base

source_channels = Table(
    'source_channels',
    Base.metadata,
    Column('source_id', Integer, ForeignKey('monitored_sources.id', ondelete='CASCADE'), primary_key=True),
    Column('channel_id', Integer, ForeignKey('output_channels.id', ondelete='CASCADE'), primary_key=True)
)
