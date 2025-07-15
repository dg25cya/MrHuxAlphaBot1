"""Script to get Telegram group ID."""
import os
import sys
import asyncio
from loguru import logger
from telethon import TelegramClient

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings

settings = get_settings()

async def get_group_id(group_username: str) -> None:
    """Get the ID of a Telegram group."""
    try:
        client = TelegramClient(
            'get_id_session',
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        await client.start()
        
        # Get the entity
        entity = await client.get_entity(group_username)
        logger.info(f"Group ID for {group_username}: {entity.id}")
        
        await client.disconnect()
        
    except Exception as e:
        logger.error(f"Error getting group ID: {e}")
        raise

if __name__ == "__main__":
    group_username = "MrHuAlphaBotPlays"
    asyncio.run(get_group_id(group_username))
