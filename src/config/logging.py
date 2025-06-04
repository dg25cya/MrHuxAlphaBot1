"""Logging configuration for the application."""
import logging
import sys
from pathlib import Path

from loguru import logger

from src.config.settings import get_settings

settings = get_settings()

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure loguru
config = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "level": settings.LOG_LEVEL,
        },
        {
            "sink": "logs/sma_telebot.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "rotation": "1 day",
            "retention": "1 month",
            "level": settings.LOG_LEVEL,
        },
    ],
}

# Remove default handler
logger.remove()

# Add configured handlers
for handler in config["handlers"]:
    logger.add(**handler)

# Intercept standard library logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

# Configure standard library logging
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Configure external libraries logging
for log_name in ["telethon", "httpx", "sqlalchemy", "alembic"]:
    logging.getLogger(log_name).setLevel(settings.LOG_LEVEL)
