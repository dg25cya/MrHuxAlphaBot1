"""Prometheus metrics collection utility."""
from functools import wraps
from typing import Any, Callable, Optional, Dict
import time
from loguru import logger
from .metrics_registry import metrics

__all__ = ['metrics']

# Utility decorators and wrappers using the central metrics registry

def track_request_duration(method: str, path: str) -> None:
    """Decorator to track API request duration."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status_code = 500  # Default to error
            try:
                result = await func(*args, **kwargs)
                status_code = getattr(result, 'status_code', 200)
                return result
            finally:
                duration = time.time() - start_time
                metrics.observe_request_duration(method, path, status_code, duration)
                metrics.log_api_request(method, path)
        return wrapper
    return decorator

def track_ws_message(direction: str = "incoming") -> None:
    """Decorator to track websocket message handling."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                metrics.log_ws_message(direction)
                return result
            except Exception as e:
                logger.error(f"Error in websocket message handling: {e}")
                raise
        return wrapper
    return decorator

def measure_latency(operation: str) -> None:
    """Decorator to measure operation latency."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metrics.observe_monitor_latency(operation, duration)
        return wrapper
    return decorator

def track_token_update(func: Callable) -> Callable:
    """Decorator to track token updates."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            result = await func(*args, **kwargs)
            metrics.log_token_update("success")
            return result
        except Exception as e:
            metrics.log_token_update("error")
            raise
    return wrapper

def track_db_operation(operation: str) -> None:
    """Decorator to track database operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                metrics.log_db_error(operation)
                raise
        return wrapper
    return decorator

# Safe metric wrappers
from prometheus_client import Counter, Gauge, Histogram

def safe_counter_inc(counter: Counter, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
    """Safely increment a counter metric."""
    try:
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)
    except Exception as e:
        logger.error(f"Failed to increment counter: {e}")

def safe_gauge_set(gauge: Gauge, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Safely set a gauge metric."""
    try:
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)
    except Exception as e:
        logger.error(f"Failed to set gauge: {e}")

def safe_histogram_observe(histogram: Histogram, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Safely observe a histogram metric."""
    try:
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)
    except Exception as e:
        logger.error(f"Failed to observe histogram: {e}")

class MetricTimer:
    """Context manager for timing operations and recording to a histogram."""
    def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]] = None) -> None:
        self.histogram = histogram
        self.labels = labels
        self.start_time = None

    def __enter__(self) -> None:
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            safe_histogram_observe(self.histogram, duration, self.labels)
