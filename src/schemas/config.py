"""Bot configuration schemas."""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from enum import Enum

class AlertLevel(str, Enum):
    """Alert severity levels."""
    critical = "critical"
    warning = "warning"
    info = "info"

class TokenMonitoringConfig(BaseModel):
    """Token monitoring thresholds configuration."""
    min_liquidity: float = Field(
        1000.0,
        description="Minimum liquidity threshold in USD"
    )
    min_volume_24h: float = Field(
        5000.0,
        description="Minimum 24h volume threshold in USD"
    )
    max_price_impact: float = Field(
        10.0,
        description="Maximum acceptable price impact percentage"
    )
    min_holder_count: int = Field(
        100,
        description="Minimum number of token holders"
    )
    max_monitoring_age: int = Field(
        30,
        description="Maximum age in days to keep monitoring a token"
    )

    @validator('min_liquidity', 'min_volume_24h')
    def validate_positive_float(cls, v) -> None:
        """Validate positive float values."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @validator('max_price_impact')
    def validate_price_impact(cls, v) -> None:
        """Validate price impact percentage."""
        if not 0 <= v <= 100:
            raise ValueError("Price impact must be between 0 and 100")
        return v

class ScoringWeights(BaseModel):
    """Token scoring weights configuration."""
    liquidity_weight: float = Field(0.3, ge=0, le=1)
    volume_weight: float = Field(0.2, ge=0, le=1)
    holders_weight: float = Field(0.15, ge=0, le=1)
    age_weight: float = Field(0.1, ge=0, le=1)
    sentiment_weight: float = Field(0.15, ge=0, le=1)
    safety_weight: float = Field(0.1, ge=0, le=1)

    @validator('*')
    def validate_weights_sum(cls, v, values) -> None:
        """Validate that weights sum to 1."""
        if values and len(values) == 5:  # Last field being validated
            total = sum(values.values()) + v
            if not 0.99 <= total <= 1.01:  # Allow small float rounding errors
                raise ValueError("Weights must sum to 1.0")
        return v

class NotificationConfig(BaseModel):
    """Notification system configuration."""
    min_score_threshold: float = Field(6.0, ge=0, le=10)
    alert_cooldown: int = Field(300, ge=60)  # Minimum 1 minute
    channels: Dict[str, bool] = Field(
        default_factory=lambda: {
            "telegram": True,
            "discord": False,
            "slack": False
        }
    )
    alert_levels: Dict[str, AlertLevel] = Field(
        default_factory=lambda: {
            "high_liquidity": AlertLevel.critical,
            "high_volume": AlertLevel.warning,
            "trending": AlertLevel.info
        }
    )

class MonitoringGroups(BaseModel):
    """Telegram group monitoring configuration."""
    group_ids: List[int] = Field(..., description="List of Telegram group IDs to monitor")
    weights: Dict[int, float] = Field(
        default_factory=dict,
        description="Group weights for scoring (default 1.0)"
    )
    blacklist: List[int] = Field(
        default_factory=list,
        description="Blacklisted group IDs"
    )

class BotConfig(BaseModel):
    """Complete bot configuration."""
    monitoring: TokenMonitoringConfig
    scoring: ScoringWeights
    notifications: NotificationConfig
    groups: MonitoringGroups
    retention_days: int = Field(90, ge=1, le=365)
    debug_mode: bool = Field(False)
    maintenance_mode: bool = Field(False)
    admin_users: List[int] = Field(
        ...,
        description="List of admin user IDs"
    )
