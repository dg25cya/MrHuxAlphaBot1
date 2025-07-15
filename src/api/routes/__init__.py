"""API routes module."""
from .dashboard_api import router as dashboard_api_router
from .health import router as health_router
from .dashboard import router as dashboard
from .metrics import router as metrics
from .websocket import router as websocket

__all__ = [
    'dashboard_api_router',
    'health_router', 
    'dashboard',
    'metrics',
    'websocket'
]
