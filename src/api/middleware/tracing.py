"""Tracing middleware for the API."""
import time
from typing import Callable
from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.metrics_registry import metrics

class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracing API requests."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process the request and add tracing."""
        method = request.method
        path = request.url.path
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            duration = time.time() - start_time
            metrics.observe_request_duration(method, path, status_code, duration)
            
            # Log slow requests
            if duration > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow request: {method} {path} "
                    f"took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            metrics.observe_request_duration(method, path, 500, duration)
            logger.error(f"Request failed: {method} {path} - {str(e)}")
            raise
