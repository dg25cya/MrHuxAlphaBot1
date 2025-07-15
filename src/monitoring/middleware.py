"""FastAPI middleware for monitoring."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.monitoring.metrics import (
    api_request_counter,
    api_request_duration,
    error_counter
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API metrics."""
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process the request and collect metrics."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record request duration
            duration = time.time() - start_time
            api_request_duration.observe(
                duration,
                {"endpoint": request.url.path}
            )
            
            # Count successful request
            api_request_counter.inc(
                1,
                {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status": str(response.status_code)
                }
            )
            
            return response
        
        except Exception as e:
            # Count failed request
            api_request_counter.inc(
                1,
                {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status": "500"
                }
            )
            
            # Record error
            error_counter.inc(
                1,
                {
                    "type": type(e).__name__,
                    "source": "api"
                }
            )
            
            raise
