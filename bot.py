"""Standalone Telegram bot service for MR HUX Alpha Bot."""
import asyncio
from loguru import logger

from src.config.settings import get_settings
from src.core.telegram.client import initialize_client
from src.core.telegram.commands import setup_command_handlers
from src.core.telegram.listener import setup_message_handler
from src.database import SessionLocal, init_db

settings = get_settings()

async def main():
    """Initialize and run the bot service."""
    try:
        logger.info("🤖 Starting MR HUX Alpha Bot Service...")
        
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize Telegram client
        client = await initialize_client()
        logger.info("✅ Telegram client initialized")
        
        # Setup database session
        db = SessionLocal()
        
        # Setup command handlers
        await setup_command_handlers(client, db)
        logger.info("✅ Command handlers initialized")
        
        # Setup message listener for monitoring groups
        await setup_message_handler(client, db)
        logger.info("✅ Message listener initialized")
        
        # Log successful startup
        logger.info("🤖 Bot service successfully started and ready!")
        if settings.bot_token:
            logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        
        # Run until disconnected
        await client.run_until_disconnected()
    
    except Exception as e:
        logger.exception(f"Fatal error in bot service: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(main()) 