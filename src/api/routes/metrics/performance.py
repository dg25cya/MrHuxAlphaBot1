"""API endpoints for monitoring performance metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta

from ....utils.db import get_db
from ....utils.metrics_registry import metrics

router = APIRouter(prefix="/monitoring/performance", tags=["monitoring"])

@router.get("")
async def get_performance_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get detailed system performance metrics."""
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)

    # Get API performance metrics
    api_latency_p95 = 0.0  # Placeholder, update with actual logic if available

    # Get database performance metrics
    db_latency_p95 = 0.0  # Placeholder, update with actual logic if available
    pool_size = 0
    used_connections = 0
    pool_usage = 0.0

    # Get token processing metrics
    token_processing_latency = 0.0  # Placeholder
    batch_insert_latency = 0.0      # Placeholder
    query_latency = 0.0             # Placeholder

    # Get WebSocket metrics
    ws_connections = 0
    ws_latency = 0.0

    # Get memory usage
    current_memory = 0

    return {
        "api": {
            "latency_p95": api_latency_p95,
            "success_rate": 100.0,
        },
        "database": {
            "query_latency_p95": db_latency_p95,
            "pool_usage_percent": pool_usage,
            "active_connections": used_connections,
        },
        "token_processing": {
            "processing_latency": token_processing_latency,
            "batch_insert_latency": batch_insert_latency,
            "query_latency": query_latency,
        },
        "websocket": {
            "active_connections": ws_connections,
            "message_latency": ws_latency,
        },
        "system": {
            "memory_usage_bytes": current_memory,
        },
        "thresholds": {
            "api_latency_threshold": 1.0,  # 1 second
            "db_latency_threshold": 0.1,   # 100ms
            "processing_latency_threshold": 5.0,  # 5 seconds
            "memory_threshold_bytes": 1e9,  # 1GB
        }
    }
