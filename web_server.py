"""Standalone web server service for MR HUX Alpha Bot."""
import asyncio
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from src.config.settings import get_settings
from src.database import init_db
from src.api.routes import health_router, dashboard, metrics, websocket, dashboard_api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("🌐 Starting MR HUX Alpha Bot Web Server...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Log successful startup
        logger.info("🌐 Web server successfully started and ready!")
        logger.info(f"🔧 Environment: {settings.env}")
        logger.info(f"📝 Log Level: {settings.log_level}")
        logger.info(f"🌐 Web Server: http://{settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.exception(f"Fatal error during web server startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down web server...")
        logger.info("✅ Web server shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MR HUX Alpha Bot Web Server",
        description="Web dashboard and API for MR HUX Alpha Bot",
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
            return {"message": "MR HUX Alpha Bot Web Server is running!", "status": "healthy"}
    
    return app

def main():
    """Run the web server."""
    app = create_app()
    
    # Use PORT environment variable for Render compatibility
    import os
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

if __name__ == "__main__":
    main() 