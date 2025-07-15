"""Settings configuration using Pydantic."""
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import timedelta

from pydantic import PostgresDsn, RedisDsn, Field, BaseModel, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=False,
        env_prefix=""
    )
    
    # Application settings
    env: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    metrics_port: int = 9090
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    prometheus_port: int = 9090
    log_level: str = "INFO"
    database_url: str = "sqlite:///mr_hux_alpha_bot.db"
    telegram_api_id: Optional[str] = None
    telegram_api_hash: Optional[str] = None
    bot_token: Optional[str] = None
    output_channel_id: Optional[int] = None
    admin_user_ids: str = ""
    
    # Rate limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60
    max_requests_per_minute: int = Field(default=60, description="Maximum API requests per minute")
    max_alerts_per_hour: int = Field(default=10, description="Maximum alerts per hour per source")
    
    # Token Monitoring
    price_alert_threshold: float = Field(default=5.0, description="Price change threshold in percent")
    volume_alert_threshold: float = Field(default=100.0, description="Volume change threshold in percent")
    holder_alert_threshold: float = Field(default=10.0, description="Holder count change threshold in percent")
    social_alert_threshold: float = Field(default=200.0, description="Social mention change threshold in percent")
    max_acceptable_tax: float = Field(default=10.0, description="Maximum acceptable tax percentage")
    whale_holder_threshold: float = Field(default=5.0, description="Maximum percentage of supply for a single holder")
    min_liquidity_usd: float = Field(default=50000.0, description="Minimum liquidity in USD")
    max_price_impact: float = Field(default=3.0, description="Maximum acceptable price impact percentage")
    min_lp_lock_days: int = Field(default=180, description="Minimum LP lock time in days")
    
    # AI/ML Settings
    min_confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold for AI predictions")
    sentiment_threshold: float = Field(default=0.3, description="Minimum sentiment score threshold")
    risk_cache_minutes: int = Field(default=30, description="Risk assessment cache duration in minutes")
    max_cache_size: int = Field(default=1000, description="Maximum size for caches")
    
    # Output Settings
    max_message_length: int = Field(default=2000, description="Maximum message length for output channels")
    max_attachments: int = Field(default=10, description="Maximum number of attachments per message")
    
    # Database settings
    redis_url: Optional[RedisDsn] = None
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # API Keys
    rugcheck_api_key: Optional[str] = None
    birdeye_api_key: Optional[str] = None
    dexscreener_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    
    # Social Media API Keys
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    discord_token: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    github_token: Optional[str] = None
    
    # X/Twitter API Keys
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_secret: Optional[str] = None
    
    # JWT Settings
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    @computed_field
    @property
    def risk_cache_ttl(self) -> timedelta:
        """Get risk cache TTL as timedelta."""
        return timedelta(minutes=self.risk_cache_minutes)

    @computed_field
    @property
    def admin_users(self) -> List[int]:
        """Get list of admin user IDs."""
        if not self.admin_user_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_user_ids.split(",") if uid.strip()]

    @field_validator("price_alert_threshold", "volume_alert_threshold", "holder_alert_threshold", 
                    "social_alert_threshold", "max_acceptable_tax", "whale_holder_threshold",
                    "min_liquidity_usd", "max_price_impact")
    def validate_positive_float(cls, v: float) -> float:
        """Validate positive float values."""
        if v < 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("min_lp_lock_days", "max_cache_size", "max_alerts_per_hour")
    def validate_positive_int(cls, v: int) -> int:
        """Validate positive integer values."""
        if v < 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("min_confidence_threshold", "sentiment_threshold")
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold values between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v


def get_settings() -> Settings:
    """Get settings instance."""
    logger.info("Loading settings from environment.")
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise


# Global settings instance
settings = get_settings()
