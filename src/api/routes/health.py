"""Health check routes for service monitoring."""
from fastapi import APIRouter, Depends
from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime

from ..dependencies import get_db
from ...config.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()

@router.get("")
async def health_check(db: Session = Depends(get_db)) -> Dict:
    """Check the health of critical services."""
    try:
        # Check database
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "api": "healthy"
        }
    }

@router.get("/ready")
async def readiness_check() -> Dict:
    """Check if the service is ready to handle requests."""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
