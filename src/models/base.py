"""Base model with common functionality."""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session

from src.utils import get_utc_now


class BaseModel:
    """Base model class with common functionality."""
    
    @declared_attr
    def __tablename__(cls) -> None:
        """Generate table name from class name."""
        return cls.__name__.lower()
        
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update model attributes from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    @classmethod
    def get_by_id(cls, db: Session, id: int) -> Optional['BaseModel']:
        """Get model instance by ID."""
        return db.query(cls).filter(cls.id == id).first()
        
    @classmethod
    def get_all(cls, db: Session, **filters) -> list['BaseModel']:
        """Get all model instances matching filters."""
        query = db.query(cls)
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        return query.all()

    def save(self, db: Session) -> None:
        """Save model instance to database."""
        if not self.id:
            db.add(self)
        db.commit()
        db.refresh(self)
        
    def delete(self, db: Session) -> None:
        """Delete model instance from database."""
        db.delete(self)
        db.commit()


Base = declarative_base(cls=BaseModel)
