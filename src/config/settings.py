"""Settings configuration using Pydantic."""
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram settings
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    BOT_TOKEN: str
    OUTPUT_CHANNEL_ID: int

    # Database settings
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    # API Keys
    RUGCHECK_API_KEY: str
    BIRDEYE_API_KEY: Optional[str] = None

    # Bot configuration
    MIN_SCORE_THRESHOLD: int = 6
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # Monitoring
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
