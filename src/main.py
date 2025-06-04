"""Main entry point for the SMA Telebot application."""
import asyncio

from loguru import logger

from src.config.logging import config  # This will initialize logging
from src.config.settings import get_settings
from src.core.telegram.client import initialize_client

settings = get_settings()

async def main():
    """Initialize and run the bot."""
    try:
        logger.info("Starting SMA Telebot...")
        
        # Initialize Telegram client
        client = await initialize_client()
        
        # Log successful startup
        logger.info("Bot successfully started!")
        
        # Run until disconnected
        await client.run_until_disconnected()
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
