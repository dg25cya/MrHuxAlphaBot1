#!/usr/bin/env python3
"""
Launch script for MR HUX Alpha Bot with both web dashboard and Telegram bot.
"""

import asyncio
import uvicorn
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.core.telegram.client import initialize_client
from src.core.telegram.commands import setup_command_handlers
from src.core.telegram.listener import setup_message_handler
from src.database import SessionLocal, init_db
from loguru import logger
from src.core.services.source_handlers import SourceManager
from src.core.services.output_service import OutputService
from src.core.services.continuous_hunter import get_play_hunter

settings = get_settings()

async def run_telegram_bot():
    """Run the Telegram bot."""
    try:
        logger.info("🤖 Starting Telegram bot...")
        await init_db()
        logger.info("✅ Database initialized")
        client = await initialize_client()
        logger.info("✅ Telegram client initialized")
        db = SessionLocal()
        await setup_command_handlers(client, db)
        logger.info("✅ Command handlers initialized")
        await setup_message_handler(client, db)
        logger.info("✅ Message listener initialized")

        # --- AUTO-START HUNTING AND OUTPUT SERVICE ---
        source_manager = SourceManager()
        output_service = OutputService(db, client)
        await output_service.start()
        hunter = get_play_hunter(source_manager, output_service)
        await hunter.start()
        logger.info("✅ Continuous hunting started (auto)")
        # ------------------------------------------------

        logger.info("🤖 Telegram bot successfully started and ready!")
        if settings.bot_token:
            logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        await client.run_until_disconnected()
    except Exception as e:
        logger.exception(f"Fatal error in Telegram bot: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

async def run_web_server():
    """Run the FastAPI web server as a coroutine."""
    try:
        logger.info("🌐 Starting web server...")
        from src.main import app
        port = int(os.environ.get("PORT", settings.port))
        logger.info(f"🌐 Web Server: http://0.0.0.0:{port}")
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.exception(f"Fatal error in web server: {e}")
        raise

async def main():
    """Main function to start both bot and web server."""
    print("🚀 MR HUX ALPHA BOT - LAUNCHING BOTH BOT AND WEB SERVER")
    print("=" * 60)
    try:
        await asyncio.gather(
            run_web_server(),
            run_telegram_bot()
        )
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown complete")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 