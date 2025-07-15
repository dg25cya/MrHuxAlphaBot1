"""Test Telegram bot credentials."""
import os
import sys
import asyncio
from loguru import logger
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings

settings = get_settings()

async def test_bot_connection():
    """Test connection to Telegram."""
    logger.info("Testing Telegram bot connection...")
    logger.info(f"API ID: {settings.telegram_api_id}")
    logger.info(f"Bot token: {settings.bot_token}")
    
    try:
        # Create client
        client = TelegramClient(
            StringSession(),
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        # Start the client
        logger.info("Starting client...")
        await client.start(bot_token=settings.bot_token)
        
        # Get bot info
        me = await client.get_me()
        logger.info(f"Successfully connected as: {me.username}")
        
        await client.disconnect()
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_bot_connection())
