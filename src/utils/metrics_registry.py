"""Centralized metrics registry for the application."""
from prometheus_client import Counter, Histogram, Gauge, REGISTRY
from loguru import logger
import threading

def clear_metrics_registry() -> None:
    """Clear the Prometheus registry to prevent duplicate metrics."""
    try:
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()
        logger.info("Prometheus registry cleared")
    except Exception as e:
        logger.warning(f"Failed to clear registry: {e}")

class MetricsRegistry:
    """Central registry for all application metrics."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> None:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        # Clear any existing metrics first
        clear_metrics_registry()
        
        # Token monitoring metrics
        self.token_updates = Counter(
            'token_updates_total',
            'Number of token updates processed',
            ['status']
        )
        self.token_price_changes = Histogram(
            'token_price_changes',
            'Distribution of token price changes',
            ['token_address'],
            buckets=[0.1, 0.5, 1, 5, 10, 50, 100]
        )
        self.monitor_latency = Histogram(
            'token_monitor_latency_seconds',
            'Latency of token monitoring operations',
            ['operation'],
            buckets=[0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.token_count = Gauge(
            'monitored_tokens_count',
            'Number of tokens being actively monitored'
        )
        self.momentum_scores = Histogram(
            'token_momentum_scores',
            'Distribution of token momentum scores',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.message_process_time = Histogram(
            'telegram_message_process_seconds',
            'Time spent processing telegram messages',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.messages_processed = Counter(
            'telegram_messages_processed_total',
            'Number of messages processed',
            ['status']
        )
        self.db_errors = Counter(
            'telegram_db_errors_total',
            'Number of database errors encountered',
            ['operation']
        )
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'Duration of API requests',
            ['method', 'path', 'status_code'],
            buckets=[0.01, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['method', 'path']
        )
        self.api_errors = Counter(
            'api_errors_total',
            'Total number of API errors',
            ['method', 'path', 'error_type']
        )
        self.ws_connections = Gauge(
            'websocket_connections_current',
            'Current number of websocket connections'
        )
        self.ws_messages = Counter(
            'websocket_messages_total',
            'Total number of websocket messages',
            ['direction']
        )
        self.service_uptime = Gauge(
            'service_uptime_seconds',
            'Service uptime in seconds'
        )
        self.service_info = Gauge(
            'service_info',
            'Service version information',
            ['version']
        )

    def log_token_update(self, status: str) -> None:
        """Log a token update with status."""
        try:
            self.token_updates.labels(status=status).inc()
        except Exception as e:
            logger.error(f"Failed to log token update: {e}")

    def record_price_change(self, token_address: str, change: float) -> None:
        """Record a token price change."""
        try:
            self.token_price_changes.labels(token_address=token_address).observe(abs(change))
        except Exception as e:
            logger.error(f"Failed to record price change: {e}")

    def observe_monitor_latency(self, operation: str, duration: float) -> None:
        """Record monitoring operation latency."""
        try:
            self.monitor_latency.labels(operation=operation).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record monitor latency: {e}")

    def update_token_count(self, delta: float = 1.0) -> None:
        """Update the number of monitored tokens."""
        try:
            self.token_count.inc(delta)
        except Exception as e:
            logger.error(f"Failed to update token count: {e}")

    def record_momentum_score(self, score: float) -> None:
        """Record a token momentum score."""
        try:
            self.momentum_scores.observe(score)
        except Exception as e:
            logger.error(f"Failed to record momentum score: {e}")

    def log_message_processed(self, status: str) -> None:
        """Log a processed message with status."""
        try:
            self.messages_processed.labels(status=status).inc()
        except Exception as e:
            logger.error(f"Failed to log message processed: {e}")

    def log_db_error(self, operation: str) -> None:
        """Log a database error for an operation."""
        try:
            self.db_errors.labels(operation=operation).inc()
        except Exception as e:
            logger.error(f"Failed to log DB error: {e}")

    def observe_request_duration(self, method: str, path: str, status_code: int, duration: float) -> None:
        """Record API request duration."""
        try:
            self.api_request_duration.labels(
                method=method,
                path=path,
                status_code=status_code
            ).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record request duration: {e}")

    def log_api_request(self, method: str, path: str) -> None:
        """Log an API request."""
        try:
            self.api_requests_total.labels(method=method, path=path).inc()
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")

    def log_api_error(self, method: str, path: str, error_type: str) -> None:
        """Log an API error."""
        try:
            self.api_errors.labels(method=method, path=path, error_type=error_type).inc()
        except Exception as e:
            logger.error(f"Failed to log API error: {e}")

    def update_ws_connections(self, delta: float = 1.0) -> None:
        """Update websocket connection count."""
        try:
            self.ws_connections.inc(delta)
        except Exception as e:
            logger.error(f"Failed to update websocket connections: {e}")

    def log_ws_message(self, direction: str) -> None:
        """Log a websocket message."""
        try:
            self.ws_messages.labels(direction=direction).inc()
        except Exception as e:
            logger.error(f"Failed to log websocket message: {e}")

    def update_service_uptime(self, uptime: float) -> None:
        """Update service uptime."""
        try:
            self.service_uptime.set(uptime)
        except Exception as e:
            logger.error(f"Failed to update service uptime: {e}")

    def set_service_info(self, version: str) -> None:
        """Set service version information."""
        try:
            self.service_info.labels(version=version).set(1)
        except Exception as e:
            logger.error(f"Failed to set service info: {e}")

def get_metrics() -> MetricsRegistry:
    """Get the singleton metrics registry instance."""
    return MetricsRegistry()

# For backward compatibility
metrics = get_metrics()
