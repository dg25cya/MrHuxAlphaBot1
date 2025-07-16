"""Telegram client setup and initialization."""
from telethon import TelegramClient
from loguru import logger
import os

from src.config.settings import get_settings

settings = get_settings()

# Use a unique session file per deployment (avoid conflicts)
SESSION_FILE = os.environ.get("TELEGRAM_SESSION_FILE", "sma_bot")

# Validate required environment variables
if not settings.telegram_api_id or not settings.telegram_api_hash or not settings.bot_token:
    raise RuntimeError("Missing Telegram API credentials: TELEGRAM_API_ID, TELEGRAM_API_HASH, or BOT_TOKEN.")

api_id = int(settings.telegram_api_id)
api_hash = str(settings.telegram_api_hash)
bot_token = str(settings.bot_token)

client = TelegramClient(
    SESSION_FILE,
    api_id,
    api_hash,
)

async def initialize_client() -> TelegramClient:
    """Initialize and start the Telegram client."""
    logger.info(f"Initializing Telegram client with session file: {SESSION_FILE}")
    try:
        if not client.is_connected():
            await client.start(bot_token=bot_token)
            logger.info("Telegram client successfully started")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Telegram client: {e}")
        raise

async def get_client() -> TelegramClient:
    """Get the current Telegram client instance."""
    if not client.is_connected():
        await initialize_client()
    return client
