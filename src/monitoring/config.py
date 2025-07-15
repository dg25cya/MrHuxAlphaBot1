"""Common monitoring configuration."""
from enum import Enum
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class MetricLabels(Enum):
    """Standard metric labels."""
    STATUS = "status"
    ENDPOINT = "endpoint"
    METHOD = "method"
    TYPE = "type"
    SOURCE = "source"
    OPERATION = "operation"
    ACTION = "action"

class MonitoringConfig(BaseSettings):
    """Monitoring configuration."""
    model_config = SettingsConfigDict(env_prefix="MONITORING_")
    PUSHGATEWAY_URL: str = "http://localhost:9091"
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"
    METRICS_PREFIX: str = "sma"
    RETENTION_DAYS: int = 30
    METRIC_LABELS: List[str] = [
        "endpoint",
        "method",
        "status",
        "type",
        "source",
        "operation",
        "action"
    ]
    DEFAULT_BUCKETS: List[float] = [
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0
    ]
