#!/usr/bin/env python3
"""
Launch script for MR HUX Alpha Bot with both web dashboard and Telegram bot.
"""

import asyncio
import uvicorn
import os
import signal
import sys
from contextlib import asynccontextmanager
from multiprocessing import Process

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from src.config.settings import get_settings
from src.core.telegram.client import initialize_client
from src.core.telegram.commands import setup_command_handlers
from src.core.telegram.listener import setup_message_handler
from src.database import SessionLocal, init_db
from src.api.routes import health_router, dashboard, metrics, websocket, dashboard_api_router
from src.core.services.continuous_hunter import ContinuousPlayHunter
from src.core.services.token_monitor import TokenMonitor
from src.core.services.source_handlers import SourceManager
from src.core.services.output_service import OutputService

settings = get_settings()

# Global variables
telegram_client = None
db_session = None
bot_process = None
web_process = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if bot_process:
        bot_process.terminate()
    if web_process:
        web_process.terminate()
    sys.exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global telegram_client, db_session
    
    # Startup
    logger.info("🚀 Starting MR HUX Alpha Bot (Combined Mode)...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize Telegram client
        telegram_client = await initialize_client()
        logger.info("✅ Telegram client initialized")
        
        # Setup database session
        db_session = SessionLocal()
        
        # Setup command handlers
        await setup_command_handlers(telegram_client, db_session)
        logger.info("✅ Command handlers initialized")
        
        # Setup message listener for monitoring groups
        await setup_message_handler(telegram_client, db_session)
        logger.info("✅ Message listener initialized")
        
        # Start background services
        source_manager = SourceManager(db_session)
        output_service = OutputService(db_session, telegram_client)
        play_hunter = ContinuousPlayHunter(source_manager, output_service)
        token_monitor = TokenMonitor()
        
        # Start background tasks
        if hasattr(play_hunter,start') and callable(play_hunter.start):
            asyncio.create_task(play_hunter.start())
        if hasattr(token_monitor,start') and callable(token_monitor.start):
            asyncio.create_task(token_monitor.start())
        logger.info("✅ Background services started")
        
        # Log successful startup
        logger.info("🤖 Bot successfully started and ready!")
        if settings.bot_token:
            logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        logger.info(f"🌐 Web Server: http://{settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.exception(f"Fatal error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down MR HUX Alpha Bot...")
        if db_session:
            db_session.close()
        if telegram_client:
            await telegram_client.disconnect()
        logger.info("✅ Shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MR HUX Alpha Bot",
        description="Advanced Solana token monitoring and alerting system",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"],     allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(health_router)
    app.include_router(dashboard)
    app.include_router(metrics)
    app.include_router(websocket)
    app.include_router(dashboard_api_router, prefix="/api")
    
    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory="src/static"), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    # Add root endpoint for dashboard
    @app.get("/")
    async def root():
        """Serve the main dashboard page."""
        try:
            return FileResponse("src/static/index.html")
        except Exception as e:
            logger.warning(f"Could not serve dashboard: {e}")
            return {"message": "MR HUX Alpha Bot is running!", "status": "healthy"}
    return app

def run_web_server():
    """Run the web server."""
    app = create_app()
    
    # Use PORT environment variable for deployment compatibility
    port = int(os.getenv("PORT", settings.port))
    host = settings.host
    
    logger.info(f"🚀 Starting web server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        access_log=True
    )

async def run_bot():
    """Run the Telegram bot."""
    try:
        logger.info("🤖 Starting Telegram bot...")
        
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
        
        # Start background services
        source_manager = SourceManager(db)
        output_service = OutputService(db, client)
        play_hunter = ContinuousPlayHunter(source_manager, output_service)
        token_monitor = TokenMonitor()
        
        # Start background tasks
        asyncio.create_task(play_hunter.start())
        asyncio.create_task(token_monitor.start())
        logger.info("✅ Background services started")
        
        # Log successful startup
        logger.info("🤖 Bot successfully started and ready!")
        if settings.bot_token:
            logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        
        # Run until disconnected
        await client.run_until_disconnected()
    
    except Exception as e:
        logger.exception(f"Fatal error in bot: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if we should run in combined mode or separate mode
    combined_mode = os.getenv("COMBINED_MODE", "true").lower() == "true"
    if combined_mode:
        logger.info("🚀 Starting in combined mode (bot + web server)")
        # Run web server in main process, bot in background
        run_web_server()
    else:
        logger.info("🚀 Starting in separate mode")
        # Run both in separate processes
        web_process = Process(target=run_web_server)
        web_process.start()
        
        # Run bot in main process
        asyncio.run(run_bot())

if __name__ == "__main__":
    main() 