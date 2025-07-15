"""Service for monitoring bot health and performance."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from loguru import logger
from prometheus_client import Counter, Gauge, Histogram
import psutil

from src.config.settings import get_settings

settings = get_settings()

# Core metrics
BOT_MESSAGES = Counter(
    'bot_messages_total',
    'Total number of bot messages processed'
)

BOT_ERRORS = Counter(
    'bot_errors_total',
    'Total number of bot errors by type',
    ['error_type']
)

# Import the bot health metric from the centralized monitoring module

SYSTEM_METRICS = Gauge(
    'system_metrics',
    'System metrics',
    ['metric_type']
)


class BotMonitor:
    """Monitor for bot health and metrics."""

    def __init__(self) -> None:
        """Initialize monitor."""
        self.message_count = 0
        self.error_count = 0
        self._message_history = []
        self._last_cleanup = datetime.utcnow()

    def track_message(self, message_type: str) -> None:
        """Track a processed message."""
        self.message_count += 1
        BOT_MESSAGES.inc()
        
        self._message_history.append({
            'timestamp': datetime.utcnow(),
            'type': message_type
        })
        
        # Cleanup old messages periodically
        if (datetime.utcnow() - self._last_cleanup).total_seconds() > 3600:
            self._cleanup_message_history()

    def log_error(self, error_type: str, error_msg: str) -> None:
        """Log an error occurrence."""
        self.error_count += 1
        BOT_ERRORS.labels(error_type=error_type).inc()
        logger.error(f"{error_type}: {error_msg}")

    def update_system_metrics(self) -> None:
        """Update system-level metrics."""
        try:
            # CPU usage
            SYSTEM_METRICS.labels(metric_type='cpu_percent').set(psutil.cpu_percent())
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_METRICS.labels(metric_type='memory_percent').set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            SYSTEM_METRICS.labels(metric_type='disk_percent').set(disk.percent)
            
            # Set overall health based on system metrics
            is_healthy = all([
                psutil.cpu_percent() < 90,
                memory.percent < 90,
                disk.percent < 90
            ])
            BOT_HEALTH.labels(component='system').set(1 if is_healthy else 0)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            BOT_HEALTH.labels(component='system').set(0)

    def _cleanup_message_history(self) -> None:
        """Clean up message history older than 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._message_history = [msg for msg in self._message_history 
                               if msg['timestamp'] > cutoff]
        self._last_cleanup = datetime.utcnow()

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "status": "healthy" if BOT_HEALTH.labels(component='system')._value == 1 else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "messages": {
                    "total": self.message_count,
                    "recent": len(self._message_history)
                },
                "errors": self.error_count,
                "system": {
                    "cpu": psutil.cpu_percent(),
                    "memory": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage('/').percent
                }
            }
        }