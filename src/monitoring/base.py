"""Base monitoring client implementation."""
import json
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Union
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, push_to_gateway
from loguru import logger

from src.monitoring.config import MonitoringConfig, MetricLabels

class MetricType(Enum):
    """Types of metrics supported."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class BaseMetric:
    """Base class for all metrics."""
    def __init__(
        self,
        name: str,
        description: str,
        type: MetricType,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ):
        self.name = name
        self.description = description
        self.type = type
        self.labels = labels or []
        self.buckets = buckets
        self._metric = None
        self._setup()

    def _setup(self) -> None:
        """Set up the Prometheus metric."""
        kwargs = {"name": self.name, "documentation": self.description}
        
        if self.labels:
            kwargs["labelnames"] = self.labels
            
        if self.type == MetricType.COUNTER:
            self._metric = Counter(**kwargs)
        elif self.type == MetricType.GAUGE:
            self._metric = Gauge(**kwargs)
        elif self.type == MetricType.HISTOGRAM:
            if self.buckets:
                kwargs["buckets"] = self.buckets
            self._metric = Histogram(**kwargs)

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

class BaseMonitoringClient:
    """Base client for collecting and pushing metrics."""
    def __init__(self, config: Optional[MonitoringConfig] = None) -> None:
        self.config = config or MonitoringConfig()
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, BaseMetric] = {}
        self._load_tokens()
        self._setup_default_metrics()

    def _load_tokens(self) -> None:
        """Load monitoring tokens from file."""
        try:
            with open("monitoring_tokens.json") as f:
                self.tokens = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load monitoring tokens: {e}")
            self.tokens = {}

    def _setup_default_metrics(self) -> None:
        """Set up default metrics that should be tracked."""
        # Process metrics
        self.process_start_time = self.create_gauge(
            "process_start_time_seconds",
            "Start time of the process since unix epoch in seconds"
        )
        self.process_start_time.set(time.time())

        # Runtime metrics
        self.runtime_info = self.create_gauge(
            "runtime_info",
            "Runtime information",
            ["version", "implementation"]
        )
        
        # Basic app metrics
        self.up = self.create_gauge(
            "up",
            "Whether the application is up (1) or down (0)"
        )
        self.up.set(1)

    def create_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> BaseMetric:
        """Create a Counter metric."""
        return self.create_metric(name, description, MetricType.COUNTER, labels)

    def create_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> BaseMetric:
        """Create a Gauge metric."""
        return self.create_metric(name, description, MetricType.GAUGE, labels)

    def create_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> BaseMetric:
        """Create a Histogram metric."""
        return self.create_metric(
            name,
            description,
            MetricType.HISTOGRAM,
            labels,
            buckets or self.config.DEFAULT_BUCKETS
        )

    def create_metric(
        self,
        name: str,
        description: str,
        type: MetricType,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> BaseMetric:
        """Create a new metric."""
        full_name = f"{self.config.METRICS_PREFIX}_{name}"
        if full_name in self.metrics:
            return self.metrics[full_name]
        
        metric = BaseMetric(
            full_name,
            description,
            type,
            labels,
            buckets
        )
        self.metrics[full_name] = metric
        return metric

    def push_metrics(self, job: str) -> None:
        """Push metrics to Pushgateway."""
        try:
            push_to_gateway(
                self.config.PUSHGATEWAY_URL,
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
        self._setup_default_metrics()
