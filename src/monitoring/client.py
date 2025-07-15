"""Bot-specific monitoring client implementation."""
from enum import Enum
from typing import Dict, List, Optional
import json
from loguru import logger

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, push_to_gateway

from src.monitoring.base import BaseMonitoringClient, MetricType
from src.monitoring.config import MonitoringConfig

class BotMonitoringClient(BaseMonitoringClient):
    """Bot-specific monitoring client."""
    def __init__(self) -> None:
        super().__init__(MonitoringConfig(METRICS_PREFIX="sma_bot"))

class MetricType(Enum):
    """Types of metrics supported."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class Metric:
    """Base class for all metrics."""
    def __init__(
        self,
        name: str,
        description: str,
        type: MetricType,
        labels: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.type = type
        self.labels = labels or []
        self._metric = None
        self._setup()

    def _setup(self) -> None:
        """Set up the Prometheus metric."""
        if self.type == MetricType.COUNTER:
            self._metric = Counter(
                self.name,
                self.description,
                self.labels
            )
        elif self.type == MetricType.GAUGE:
            self._metric = Gauge(
                self.name,
                self.description,
                self.labels
            )
        elif self.type == MetricType.HISTOGRAM:
            self._metric = Histogram(
                self.name,
                self.description,
                self.labels
            )

    def inc(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment counter or gauge."""
        if labels:
            self._metric.labels(**labels).inc(value)
        else:
            self._metric.inc(value)

    def dec(self, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Decrement gauge."""
        if self.type != MetricType.GAUGE:
            raise ValueError("dec() only supported for gauges")
        
        if labels:
            self._metric.labels(**labels).dec(value)
        else:
            self._metric.dec(value)

    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """Set gauge value."""
        if self.type != MetricType.GAUGE:
            raise ValueError("set() only supported for gauges")
        
        if labels:
            self._metric.labels(**labels).set(value)
        else:
            self._metric.set(value)

    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """Observe histogram value."""
        if self.type != MetricType.HISTOGRAM:
            raise ValueError("observe() only supported for histograms")
        
        if labels:
            self._metric.labels(**labels).observe(value)
        else:
            self._metric.observe(value)

class MonitoringClient:
    """Client for collecting and pushing metrics."""
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Metric] = {}
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load monitoring tokens from file."""
        try:
            with open("monitoring_tokens.json") as f:
                self.tokens = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load monitoring tokens: {e}")
            self.tokens = {}

    def create_metric(
        self,
        name: str,
        description: str,
        type: MetricType,
        labels: Optional[List[str]] = None
    ) -> Metric:
        """Create a new metric."""
        if name in self.metrics:
            return self.metrics[name]
        
        metric = Metric(name, description, type, labels)
        self.metrics[name] = metric
        return metric

    def push_metrics(self, job: str) -> None:
        """Push metrics to Pushgateway."""
        try:
            push_to_gateway(
                f"http://localhost:9091",
                job=job,
                registry=self.registry
            )
            logger.debug(f"Successfully pushed metrics for job {job}")
        except Exception as e:
            logger.error(f"Failed to push metrics for job {job}: {e}")

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.registry = CollectorRegistry()
        self.metrics.clear()

_client: Optional[MonitoringClient] = None

def get_monitoring_client() -> MonitoringClient:
    """Get the global monitoring client instance."""
    global _client
    if _client is None:
        _client = MonitoringClient()
    return _client
