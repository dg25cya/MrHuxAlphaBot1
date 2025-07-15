"""Database initialization script."""
import asyncio
import sys
from loguru import logger

from src.models.base import Base
from src.database import engine, init_db

async def setup_database():
    """Initialize the database tables."""
    logger.info("Initializing database...")
    
    try:
        # Initialize database connection
        await init_db()
        logger.info("Database connection established")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)
