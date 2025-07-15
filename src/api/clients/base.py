"""Base API client implementation."""
from typing import Any, Dict, Optional
import asyncio
from functools import wraps
from datetime import datetime, timedelta
import json

import httpx
from loguru import logger

from src.config.settings import get_settings

settings = get_settings()

# Import centralized metrics
from src.utils.metrics_registry import metrics

def retry_on_error(max_retries: int = 3, delay: float = 1.0) -> None:
    """Retry decorator for API calls."""
    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        delay_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"API call failed, retrying in {delay_time}s... Error: {e}")
                        await asyncio.sleep(delay_time)
            
            logger.error(f"API call failed after {max_retries} attempts. Last error: {last_error}")
            raise last_error
        return wrapper
    return decorator

class RateLimiter:
    """Enhanced rate limiter implementation."""
    
    def __init__(self, calls: int, period: float) -> None:
        self.calls = calls
        self.period = period
        self.timestamps = []
        self.waiting = 0  # Count of waiting requests

    async def acquire(self):
        """Acquire rate limit token with better queue management."""
        now = datetime.utcnow().timestamp()
        
        # Remove old timestamps
        self.timestamps = [ts for ts in self.timestamps if ts > now - self.period]
        
        if len(self.timestamps) >= self.calls:
            self.waiting += 1
            try:
                # Calculate wait time
                oldest = self.timestamps[0]
                wait_time = (oldest + self.period) - now
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                
                # Clean up again after waiting
                now = datetime.utcnow().timestamp()
                self.timestamps = [ts for ts in self.timestamps if ts > now - self.period]
            finally:
                self.waiting -= 1
        
        self.timestamps.append(now)

    @property
    def available(self) -> int:
        """Get number of available calls."""
        now = datetime.utcnow().timestamp()
        self.timestamps = [ts for ts in self.timestamps if ts > now - self.period]
        return self.calls - len(self.timestamps)

class BaseAPIClient:
    """Enhanced base API client with monitoring."""
    
    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        rate_limit_calls: int = 100,
        rate_limit_period: float = 60.0,
        timeout: float = 10.0,
        cache_ttl: int = 300  # 5 minutes default cache TTL
    ):
        self.name = name
        self.base_url = base_url
        self.rate_limiter = RateLimiter(rate_limit_calls, rate_limit_period)
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._cache = {}
        self._cache_ttl = cache_ttl
        self._health_check_interval = 60  # Health check every minute
        self._last_health_check = datetime.min
        self._is_healthy = True

    async def close(self):
        """Close the client session."""
        await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make an API request with caching and monitoring."""
        if cache_key and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if datetime.utcnow() < cache_entry["expires"]:
                return cache_entry["data"]
        
        # Acquire rate limit token
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        start_time = datetime.utcnow()
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers
            )
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.api_request_duration.labels(
                method=method,
                path=endpoint,
                status_code=response.status_code
            ).observe(duration)
            metrics.api_requests_total.labels(
                method=method,
                path=endpoint
            ).inc()
            
            # Handle common error cases
            response.raise_for_status()
            data = response.json()
            
            # Cache successful response if cache_key provided
            if cache_key:
                self._cache[cache_key] = {
                    "data": data,
                    "expires": datetime.utcnow() + timedelta(seconds=self._cache_ttl)
                }
            
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name} API error: {e.response.status_code} - {e.response.text}")
            self._is_healthy = False
            raise
        except httpx.RequestError as e:
            logger.error(f"{self.name} request error: {str(e)}")
            self._is_healthy = False
            raise
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} JSON decode error: {str(e)}")
            self._is_healthy = False
            raise ValueError(f"Invalid JSON response from {self.name} API")

    async def health_check(self) -> bool:
        """Check API health status."""
        now = datetime.utcnow()
        if (now - self._last_health_check).total_seconds() < self._health_check_interval:
            return self._is_healthy
        
        self._last_health_check = now
        try:
            await self._check_health_endpoint()
            self._is_healthy = True
            return True
        except Exception as e:
            logger.error(f"{self.name} health check failed: {str(e)}")
            self._is_healthy = False
            return False

    async def _check_health_endpoint(self):
        """Implement in subclasses to check specific health endpoint."""
        raise NotImplementedError("Health check endpoint not implemented")

    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """Clear the cache, optionally only entries matching the pattern."""
        if pattern:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(pattern)}
        else:
            self._cache.clear()

    @property
    def rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            "available_calls": self.rate_limiter.available,
            "waiting_requests": self.rate_limiter.waiting,
            "period": self.rate_limiter.period,
            "max_calls": self.rate_limiter.calls
        }
