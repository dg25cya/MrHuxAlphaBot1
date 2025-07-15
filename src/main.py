"""Main entry point for the MR HUX Alpha Bot application."""
import asyncio
from contextlib import asynccontextmanager

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

settings = get_settings()

# Global variables for Telegram client and database
telegram_client = None
db_session = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global telegram_client, db_session
    
    # Startup
    logger.info("🚀 Starting MR HUX Alpha Bot...")
    
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
    app.include_router(dashboard_api_router)
    
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

# Create the FastAPI app
app = create_app()

async def main():
    """Initialize and run the bot."""
    try:
        logger.info("Starting MR HUX Alpha Bot...")
        
        # Initialize Telegram client
        client = await initialize_client()
        
        # Setup database session
        db = SessionLocal()
        
        # Setup command handlers
        await setup_command_handlers(client, db)
        logger.info("✅ Command handlers initialized")
        
        # Setup message listener for monitoring groups
        await setup_message_handler(client, db)
        logger.info("✅ Message listener initialized")
        
        # Log successful startup
        logger.info("🤖 Bot successfully started and ready!")
        if settings.bot_token:
            logger.info(f"📊 Bot Token: {settings.bot_token[:10]}...")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        
        # Run until disconnected
        await client.run_until_disconnected()
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(main())
