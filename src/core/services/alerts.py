"""Alert service for token notifications."""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select, desc

from ...config.settings import get_settings
from ...models import Alert
from ...core.telegram.poster import AlertPoster
from ...api.websocket import ws_manager

# Import centralized metrics
from src.utils.metrics_registry import metrics

class AlertService:
    """Service for handling token alerts and notifications."""
    
    def __init__(self) -> None:
        """Initialize the alert service."""
        self.settings = get_settings()
        self.poster = AlertPoster()
        self._running = False
        self._alert_task = None
        self._alert_queue = asyncio.Queue()
        self._db = None
    
    async def start(self):
        """Start the alert service."""
        if self._running:
            return
            
        self._running = True
        await self.poster.initialize()
        self._alert_task = asyncio.create_task(self._process_alerts())
        logger.info("Alert service started")
    
    async def stop(self):
        """Stop the alert service."""
        if not self._running:
            return
            
        self._running = False
        if self._alert_task:
            await self._alert_task
        logger.info("Alert service stopped")
    
    async def send_alert(
        self,
        alert_data: Dict[str, Any],
        alert_type: str = "new_token"
    ):
        """Queue an alert for processing."""
        await self._alert_queue.put({
            "data": alert_data,
            "type": alert_type,
            "timestamp": datetime.utcnow()
        })
    
    async def _process_alerts(self):
        """Process alerts from the queue."""
        while self._running:
            try:
                alert = await self._alert_queue.get()
                
                # Process the alert
                try:
                    await self._handle_alert(alert)
                except Exception as e:
                    logger.error(f"Error handling alert: {e}")
                
                self._alert_queue.task_done()
                
            except Exception as e:
                logger.exception(f"Error processing alert: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _handle_alert(self, alert: Dict[str, Any]):
        """Handle a single alert."""
        try:
            alert_type = alert["type"]
            data = alert["data"]
            timestamp = alert["timestamp"]
            
            # Format basic alert message
            message = f"New token alert: {data.get('address', 'Unknown')}"
            
            # Store in database
            db_alert = Alert(
                token_id=data.get("token_id"),
                alert_type=alert_type,
                message=message,
                metrics_snapshot=data,
                created_at=timestamp
            )
            
            # Use synchronous session for now
            from ...database import SessionLocal
            db = SessionLocal()
            try:
                db.add(db_alert)
                db.commit()
                db.refresh(db_alert)
            finally:
                db.close()
            
            # Broadcast via WebSocket
            await ws_manager.broadcast_alert({
                "type": alert_type,
                "data": data,
                "message": message,
                "timestamp": timestamp.isoformat()
            })
            
            # Use centralized metrics - alert tracking will be handled by metrics registry
            pass
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
            raise
    
    async def get_recent_alerts(
        self,
        limit: int = 50,
        token_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent alerts with optional token filtering."""
        from ...database import SessionLocal
        from ...models.token import Token
        
        # Use synchronous session for now
        db = SessionLocal()
        try:
            query = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit)
            
            if token_address:
                token = db.query(Token).filter(Token.address == token_address).first()
                if token:
                    query = query.filter(Alert.token_id == token.id)
                else:
                    return []
            
            alerts = query.all()
            
            # Convert to dicts
            return [{
                "id": alert.id,
                "token_id": alert.token_id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "created_at": alert.created_at.isoformat() if alert.created_at is not None else None,
                "metrics": alert.metrics if hasattr(alert, 'metrics') else {}
            } for alert in alerts]
        finally:
            db.close()
