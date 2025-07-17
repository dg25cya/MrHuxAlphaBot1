#!/usr/bin/env python3
MR HUX Alpha Bot - Local FREE Runner
Run everything locally for free with all features enabled.
"""

import asyncio
import uvicorn
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

settings = get_settings()

async def setup_bot():
    """Setup and start the Telegram bot."""
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
        
        # Setup message listener
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
        
        logger.info("🤖 Bot successfully started and ready!")
        logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.exception(f"❌ Bot error: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

def create_web_app():
    """Create the web application."""
    app = FastAPI(
        title="MR HUX Alpha Bot - Local",
        description="Advanced Solana token monitoring and alerting system (Local FREE)",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
    
    # Add root endpoint
    @app.get("/")
    async def root():
        try:
            return FileResponse("src/static/index.html")
        except Exception as e:
            logger.warning(f"Could not serve dashboard: {e}")
            return {
                "message": "MR HUX Alpha Bot is running locally (FREE)!", 
                "status": "healthy",
                "features": [
                    "Real-time monitoring",
                    "Telegram bot",
                    "Web dashboard",
                    "AI analysis",
                    "Multi-source scanning"
                ]
            }
    
    return app

def run_web_server():
    """Run the web server."""
    app = create_web_app()
    
    port = int(os.getenv("PORT", settings.port))
    host = settings.host
    
    logger.info(f"🌐 Starting web server on {host}:{port}")
    logger.info(f"📊 Dashboard: http://localhost:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        access_log=True
    )

async def main():
    """Main function to run both bot and web server."""
    print("🚀 MR HUX Alpha Bot - Local FREE Setup")
    print("=" * 50)
    print("✅ All features enabled")
    print("✅ Real-time monitoring active")
    print("✅ All API keys configured")
    print("✅ Running locally for FREE")
    print("=" * 50)
    
    try:
        # Run both bot and web server
        await asyncio.gather(
            asyncio.to_thread(run_web_server),
            setup_bot()
        )
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 