"""Script to add the group as a notification channel."""
import asyncio
from loguru import logger
from telethon import TelegramClient
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings
from src.database import SessionLocal
from src.models.notification_channel import NotificationChannel

settings = get_settings()

async def setup_notification_channel(group_username: str) -> None:
    """Get group info and set up notification channel."""
    try:
        # Initialize Telegram client with bot token
        client = TelegramClient(
            'bot_session',
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        await client.start(bot_token=settings.bot_token)
        
        # Get the group entity
        group = await client.get_entity(group_username)
        logger.info(f"Found group: {group.title} (ID: {group.id})")
        
        # Add to notification channels
        with SessionLocal() as db:
            channel = NotificationChannel(
                channel_id=group.id,
                name=group.title,
                type="telegram",
                is_active=True,
                is_alerts=True,
                is_stats=True,
                include_stats=True,
                include_links=True,
                messages_per_minute=20,
                emoji_style="default"
            )
            
            db.merge(channel)
            db.commit()
            logger.info(f"Successfully configured notification channel for {group.title}")
        
        await client.disconnect()
        
    except Exception as e:
        logger.error(f"Error setting up notification channel: {e}")
        raise

if __name__ == "__main__":
    group_username = "MrHuAlphaBotPlays"
    asyncio.run(setup_notification_channel(group_username))
