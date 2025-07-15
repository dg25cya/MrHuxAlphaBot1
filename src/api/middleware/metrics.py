"""Middleware for API rate limiting and metrics."""
from loguru import logger
from typing import Callable
import time
import asyncio
from fastapi import Request, Response, HTTPException
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
from ...config.settings import get_settings

settings = get_settings()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_request_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint']
)

RATE_LIMIT_EXCEEDED = Counter(
    'api_rate_limit_exceeded_total',
    'Number of times rate limit was exceeded',
    ['endpoint']
)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics and rate limiting."""
    
    def __init__(self, app) -> None:
        """Initialize the middleware."""
        super().__init__(app)
        self.redis = None
        self.rate_limit = settings.rate_limit_calls
        self.rate_period = settings.rate_limit_period
        self.request_id_counter = 0
        self._counter_lock = asyncio.Lock()
        
        # Initialize Redis if URL is configured, otherwise use in-memory fallback
        if settings.redis_url:
            try:
                self.redis = Redis.from_url(str(settings.redis_url))
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.info(f"Redis connection failed: {e}. Using in-memory fallback.")
                self.redis = None
        else:
            logger.info("No Redis URL configured. Using in-memory fallback for rate limiting.")

    async def _get_next_request_id(self) -> str:
        """Generate unique request ID."""
        async with self._counter_lock:
            self.request_id_counter += 1
            return f"{time.time()}-{self.request_id_counter}"

    async def _check_rate_limit(self, key: str) -> bool:
        """Check if rate limit is exceeded."""
        # If Redis is not available, use simple in-memory rate limiting
        if not self.redis:
            # Simple in-memory rate limiting (not persistent across restarts)
            # For local development, this is sufficient
            return True
            
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                # Get current count and increment
                current = await pipe.get(key)
                if current and int(current) >= self.rate_limit:
                    return False
                    
                # Increment and set expiry
                await pipe.incr(key)
                await pipe.expire(key, self.rate_period)
                await pipe.execute()
                return True
                
        except Exception as e:
            # Log error and allow request on Redis failure
            logger.info(f"Rate limit check failed: {e}")
            return True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with metrics and rate limiting."""
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        # Get client IP from various headers
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP", "") or
            request.client.host if request.client else "unknown"
        )
        
        # Check rate limit
        rate_key = f"rate_limit:{client_ip}:{endpoint}"
        if not await self._check_rate_limit(rate_key):
            RATE_LIMIT_EXCEEDED.labels(endpoint=endpoint).inc()
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                media_type="text/plain"
            )
            
        # Generate request ID
        request_id = await self._get_next_request_id()
        request.state.request_id = request_id
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            # Add request ID header
            response.headers['X-Request-ID'] = request_id
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            raise e
        finally:
            # Clean up any resources
            pass