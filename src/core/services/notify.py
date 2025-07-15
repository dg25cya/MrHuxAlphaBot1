"""Notification service for sending alerts and messages."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from loguru import logger
from sqlalchemy.orm import Session

from src.models.alert import Alert
from src.models.notification_channel import NotificationChannel
# from src.utils.exceptions import NotificationError  # Not defined yet


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(Enum):
    """Alert types."""
    PRICE_MOVE = "price_move"
    VOLUME_SPIKE = "volume_spike"
    SECURITY_RISK = "security_risk"
    SYSTEM_ERROR = "system_error"


class AlertSource(Enum):
    """Alert sources."""
    PRICE_MONITOR = "price_monitor"
    VOLUME_MONITOR = "volume_monitor"
    SECURITY_SCANNER = "security_scanner"
    SYSTEM_MONITOR = "system_monitor"


class AlertNotification:
    """Represents a notification about an alert."""
    
    def __init__(self, title: str, message: str, severity: AlertSeverity, 
                 alert_type: AlertType, source: AlertSource, token_address: str = "",
                 token_symbol: str = "", mention_count: int = 0, 
                 metrics_snapshot: Dict[str, Any] = None, details: Dict[str, Any] = None):
        self.title = title
        self.message = message
        self.severity = severity
        self.alert_type = alert_type
        self.source = source
        self.token_address = token_address
        self.token_symbol = token_symbol
        self.mention_count = mention_count
        self.metrics_snapshot = metrics_snapshot or {}
        self.details = details or {}
        self.timestamp = datetime.now()
        self.sent = False
        self.error = None
    
    @staticmethod
    def get_severity_emoji(severity: AlertSeverity) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.INFO: "ℹ️"
        }
        return emoji_map.get(severity, "ℹ️")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "alert_type": self.alert_type.value,
            "source": self.source.value,
            "token_address": self.token_address,
            "token_symbol": self.token_symbol,
            "mention_count": self.mention_count,
            "metrics_snapshot": self.metrics_snapshot,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "sent": self.sent,
            "error": self.error
        }


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_alert_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send an alert notification to a specific channel."""
        try:
            notification = AlertNotification(alert, channel)
            
            # TODO: Implement actual notification sending logic
            # This is a placeholder for the actual implementation
            
            notification.sent = True
            logger.info(f"Sent alert notification {alert.id} to channel {channel.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
            return False
    
    async def send_bulk_notifications(self, notifications: List[AlertNotification]) -> Dict[str, int]:
        """Send multiple notifications and return results."""
        results = {"success": 0, "failed": 0}
        
        for notification in notifications:
            success = await self.send_alert_notification(notification.alert, notification.channel)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
