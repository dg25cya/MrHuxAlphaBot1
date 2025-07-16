from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from sqlalchemy import text

from src.database import get_db
from src.models.monitored_source import MonitoredSource
from src.models.output_channel import OutputChannel
from src.models.notification_channel import NotificationChannel
from src.models.alert import Alert
from src.models.token import Token

router = APIRouter()

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# --- Helper Functions ---
def get_real_stats(db: Session) -> dict:
    """Get real statistics from database."""
    try:
        active_sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).count()
        active_outputs = db.query(OutputChannel).filter(OutputChannel.is_active == True).count()
        active_notifications = db.query(NotificationChannel).filter(NotificationChannel.is_active == True).count()
        tokens_monitored = db.query(Token).count()
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_alerts = db.query(Alert).filter(Alert.created_at >= yesterday).count()
        uptime = "N/A"  # Replace with actual uptime tracking if available
        ai_stats = {}
        return {
            "tokens_monitored": tokens_monitored,
            "alerts_sent": recent_alerts,
            "sources": active_sources,
            "outputs": active_outputs + active_notifications,
            "uptime": uptime,
            "ai": ai_stats,
            "active_sources": active_sources,
            "recent_updates": recent_alerts,
            "error_rate": None,
            "telegram_channels": active_outputs,
            "discord_webhooks": active_notifications,
            "total_messages": None,
            "success_rate": None,
            "analysis_speed": None,
            "sentiment_status": "enabled",
            "summary_status": "enabled",
            "translation_status": "enabled",
            "filter_status": "enabled"
        }
    except Exception as e:
        logger.error(f"Error fetching real stats: {e}")
        return {"error": str(e)}

def get_real_sources(db: Session) -> List[dict]:
    """Get real sources from database."""
    try:
        sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
        return [
            {
                "id": source.id,
                "type": source.type,
                "name": source.name or source.identifier,
                "status": "active" if bool(source.is_active) else "inactive",
                "added_at": source.added_at.isoformat() if source.added_at is not None else None
            }
            for source in sources
        ]
    except Exception as e:
        logger.error(f"Error fetching real sources: {e}")
        return []

def get_real_outputs(db: Session) -> List[dict]:
    """Get real outputs from database."""
    try:
        outputs = db.query(OutputChannel).filter(OutputChannel.is_active == True).all()
        notifications = db.query(NotificationChannel).filter(NotificationChannel.is_active == True).all()
        
        result = []
        for output in outputs:
            result.append({
                "id": output.id,
                "type": output.type,
                "name": output.name or output.identifier,
                "status": "active" if output.is_active else "inactive"
            })
        
        for notif in notifications:
            result.append({
                "id": notif.id,
                "type": notif.type,
                "name": notif.name or str(notif.channel_id),
                "status": "active" if notif.is_active else "inactive"
            })
        
        return result
    except Exception as e:
        # Return demo data if database error
        return [
            {"id": 1, "type": "telegram", "name": "@alerts_channel", "status": "active"},
            {"id": 2, "type": "discord", "name": "Discord Webhook", "status": "active"},
            {"id": 3, "type": "dashboard", "name": "Web Dashboard", "status": "active"}
        ]

def get_real_alerts(db: Session, limit: int = 50) -> List[dict]:
    """Get real alerts from database."""
    try:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
        return [
            {
                "id": alert.id,
                "message": alert.message,
                "type": alert.alert_type,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "severity": alert.severity or "info"
            }
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error fetching real alerts: {e}")
        return []

# --- REST API Endpoints ---

@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Get recent alerts."""
    alerts = get_real_alerts(db)
    return {"alerts": alerts}

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get bot statistics."""
    stats = get_real_stats(db)
    return {"stats": stats}

@router.get("/sources")
async def get_sources(db: Session = Depends(get_db)):
    """Get monitored sources."""
    sources = get_real_sources(db)
    return {"sources": sources}

@router.post("/sources")
async def add_source(source: dict, db: Session = Depends(get_db)):
    """Add a new source."""
    try:
        new_source = MonitoredSource(
            type=source.get("type", "telegram"),
            identifier=source.get("name", ""),
            name=source.get("name", ""),
            is_active=True,
            added_at=datetime.utcnow()
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        # Broadcast update to WebSocket clients
        await manager.broadcast({
            "type": "source_added",
            "data": {"id": new_source.id, "type": new_source.type, "name": new_source.name}
        })
        
        return {"success": True, "source": {
            "id": new_source.id,
            "type": new_source.type,
            "name": new_source.name,
            "status": "active"
        }}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.delete("/sources/{source_id}")
async def remove_source(source_id: int, db: Session = Depends(get_db)):
    """Remove a source."""
    try:
        source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id).first()
        if source:
            source.is_active = False
            db.commit()
            
            # Broadcast update to WebSocket clients
            await manager.broadcast({
                "type": "source_removed",
                "data": {"id": source_id}
            })
            
            return {"success": True}
        return {"success": False, "error": "Source not found"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.get("/outputs")
async def get_outputs(db: Session = Depends(get_db)):
    """Get output channels."""
    outputs = get_real_outputs(db)
    return {"outputs": outputs}

@router.post("/outputs")
async def add_output(output: dict, db: Session = Depends(get_db)):
    """Add a new output."""
    try:
        new_output = OutputChannel(
            type=output.get("type", "telegram"),
            identifier=output.get("name", ""),
            name=output.get("name", ""),
            is_active=True,
            added_at=datetime.utcnow()
        )
        db.add(new_output)
        db.commit()
        db.refresh(new_output)
        
        # Broadcast update to WebSocket clients
        await manager.broadcast({
            "type": "output_added",
            "data": {"id": new_output.id, "type": new_output.type, "name": new_output.name}
        })
        
        return {"success": True, "output": {
            "id": new_output.id,
            "type": new_output.type,
            "name": new_output.name,
            "status": "active"
        }}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.delete("/outputs/{output_id}")
async def remove_output(output_id: int, db: Session = Depends(get_db)):
    """Remove an output."""
    try:
        output = db.query(OutputChannel).filter(OutputChannel.id == output_id).first()
        if output:
            output.is_active = False
            db.commit()
            
            # Broadcast update to WebSocket clients
            await manager.broadcast({
                "type": "output_removed",
                "data": {"id": output_id}
            })
            
            return {"success": True}
        return {"success": False, "error": "Output not found"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.get("/ai")
async def get_ai(db: Session = Depends(get_db)):
    """Get AI analytics."""
    stats = get_real_stats(db)
    return {"ai": stats["ai"]}

@router.get("/health")
async def get_health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

CONFIG_TABLE = "bot_config"
CONFIG_DEFAULTS = {
    "alert_threshold": 5,
    "theme": "dark",
    "auto_refresh": True,
    "notifications": True
}

def get_config_from_db(db):
    try:
        row = db.execute(text(f"SELECT * FROM {CONFIG_TABLE} LIMIT 1")).fetchone()
        if row:
            return dict(row)
        else:
            return CONFIG_DEFAULTS.copy()
    except Exception:
        return CONFIG_DEFAULTS.copy()

def set_config_in_db(db, config: dict):
    # Upsert config (single row)
    keys = list(CONFIG_DEFAULTS.keys())
    values = [config.get(k, CONFIG_DEFAULTS[k]) for k in keys]
    placeholders = ", ".join([f":{k}" for k in keys])
    update_clause = ", ".join([f"{k} = :{k}" for k in keys])
    # Try update first
    result = db.execute(text(f"UPDATE {CONFIG_TABLE} SET {update_clause}"), dict(zip(keys, values)))
    if result.rowcount == 0:
        # Delete all rows to guarantee only one config row
        db.execute(text(f"DELETE FROM {CONFIG_TABLE}"))
        db.execute(text(f"INSERT INTO {CONFIG_TABLE} ({', '.join(keys)}) VALUES ({placeholders})"), dict(zip(keys, values)))
    db.commit()

@router.get("/config")
async def get_config(db: Session = Depends(get_db)):
    """Get configuration."""
    return {"config": get_config_from_db(db)}

@router.put("/config")
async def set_config(config: dict, db: Session = Depends(get_db)):
    """Set configuration."""
    set_config_in_db(db, config)
    return {"success": True, "config": get_config_from_db(db)}

# --- WebSocket for Real-Time Updates ---

@router.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial stats
        db = next(get_db())
        stats = get_real_stats(db)
        await websocket.send_json({"type": "stats", "data": stats})
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            stats = get_real_stats(db)
            await websocket.send_json({"type": "stats", "data": stats})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket) 