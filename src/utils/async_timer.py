"""Async timer utilities for metrics."""
import time
from typing import Any, Callable, Awaitable, TypeVar
from contextlib import asynccontextmanager
from functools import wraps

T = TypeVar('T')

@asynccontextmanager
async def async_timer(metric):
    """Async context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metric.observe(duration)

def async_timed(metric) -> None:
    """Decorator for timing async functions."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metric.observe(duration)
        return wrapper
    return decorator
