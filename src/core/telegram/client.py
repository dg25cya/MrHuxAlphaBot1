"""Telegram client setup and initialization."""
from telethon import TelegramClient
from loguru import logger

from src.config.settings import get_settings

settings = get_settings()

# Initialize the client with API credentials
client = TelegramClient(
    'sma_bot',
    settings.telegram_api_id,
    settings.telegram_api_hash,
)

async def initialize_client() -> TelegramClient:
    """Initialize and start the Telegram client."""
    logger.info("Initializing Telegram client...")
    
    if not client.is_connected():
        await client.start(bot_token=settings.bot_token)
        logger.info("Telegram client successfully started")
    
    return client

async def get_client() -> TelegramClient:
    """Get the current Telegram client instance."""
    if not client.is_connected():
        await initialize_client()
    return client
