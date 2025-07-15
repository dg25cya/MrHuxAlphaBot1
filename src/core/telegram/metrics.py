"""Metrics handling for the Telegram listener component."""
import time
from prometheus_client import Counter, Histogram, CollectorRegistry
from loguru import logger

# Create a registry for Telegram metrics
registry = CollectorRegistry()

# Initialize metrics
MESSAGE_PROCESS_TIME = Histogram(
    'telegram_message_process_seconds',
    'Time spent processing telegram messages',
    registry=registry,
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

MESSAGES_PROCESSED = Counter(
    'telegram_messages_processed_total',
    'Number of messages processed',
    ['status'],
    registry=registry
)

DB_ERRORS = Counter(
    'telegram_db_errors_total',
    'Number of database errors encountered',
    ['operation'],
    registry=registry
)

def log_message_processed(status: str) -> None:
    """Log a processed message with its status."""
    try:
        MESSAGES_PROCESSED.labels(status=status).inc()
    except Exception as e:
        logger.warning(f"Error recording message processed metric: {e}")

def log_db_error(operation: str) -> None:
    """Log a database error for a specific operation."""
    try:
        DB_ERRORS.labels(operation=operation).inc()
    except Exception as e:
        logger.warning(f"Error recording DB error metric: {e}")

class MessageProcessTimer:
    """Context manager for timing message processing."""
    
    def __enter__(self) -> None:
        """Start timing."""
        self._start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Record processing time."""
        try:
            duration = time.time() - self._start_time
            MESSAGE_PROCESS_TIME.observe(duration)
        except Exception as e:
            logger.warning(f"Error recording message process time: {e}")

# Convenience function for timing context
def time_message_processing() -> None:
    """Get a context manager for timing message processing."""
    return MessageProcessTimer()
