"""Script to add a new notification channel."""
import asyncio
from loguru import logger
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.notification_channel import NotificationChannel


async def add_telegram_channel(channel_id: int, name: str) -> None:
    """Add a new Telegram channel to the notification channels."""
    try:
        with SessionLocal() as db:
            # Check if channel already exists
            existing = db.query(NotificationChannel).filter(
                NotificationChannel.channel_id == channel_id
            ).first()
            
            if existing:
                logger.info(f"Channel {name} already exists, updating configuration...")
                existing.is_active = True
                existing.name = name
                db.commit()
                logger.info(f"Updated channel {name}")
                return
            
            # Create new channel
            channel = NotificationChannel(
                channel_id=channel_id,
                name=name,
                type="telegram",
                is_active=True,
                is_alerts=True,
                is_stats=True,
                include_stats=True,
                include_links=True,
                messages_per_minute=20,
                emoji_style="default"
            )
            
            db.add(channel)
            db.commit()
            logger.info(f"Successfully added channel {name}")
            
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        raise


if __name__ == "__main__":
    # The group ID from https://t.me/MrHuAlphaBotPlays
    channel_name = "Mr Hux Alpha Bot Plays"
    channel_id = -1001234567890  # This needs to be replaced with the actual group ID
    
    asyncio.run(add_telegram_channel(channel_id, channel_name))
