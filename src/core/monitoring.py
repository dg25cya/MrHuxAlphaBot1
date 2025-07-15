"""Core monitoring metrics for tracking bot performance."""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import psutil
import os
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    REGISTRY
)

# Metrics Collector
class MetricsCollector:
    """Collect and manage all monitoring metrics."""
    
    def __init__(self, registry=None):
        self.token_metrics = TokenProcessingMetrics()
        self.message_metrics = MessageProcessingMetrics()
        self.alert_metrics = AlertGenerationMetrics()
        self.api_metrics = APIRequestMetrics()
        self.health_metrics = BotHealthMetrics()
        self.registry = registry or REGISTRY
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            "token_processing": self.token_metrics,
            "message_processing": self.message_metrics,
            "alert_generation": self.alert_metrics,
            "api_requests": self.api_metrics,
            "bot_health": self.health_metrics
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.token_metrics = TokenProcessingMetrics()
        self.message_metrics = MessageProcessingMetrics()
        self.alert_metrics = AlertGenerationMetrics()
        self.api_metrics = APIRequestMetrics()
        self.health_metrics = BotHealthMetrics()


# Token Processing Metrics
class TokenProcessingMetrics:
    """Track token processing performance."""
    
    def __init__(self) -> None:
        self.processing_times = defaultdict(list)
        self.validation_counts = defaultdict(int)
        self.validation_success = defaultdict(int)
        self.tokens_by_source = defaultdict(lambda: defaultdict(int))
        
    def record_processing_time(self, duration: float, timestamp: datetime = None) -> None:
        """Record token processing duration."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.processing_times[timestamp.date()].append(duration)
        
    def record_validation(self, success: bool, source: str, timestamp: datetime = None) -> None:
        """Record token validation attempt."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        date = timestamp.date()
        self.validation_counts[date] += 1
        if success:
            self.validation_success[date] += 1
        self.tokens_by_source[date][source] += 1
        
    def get_average(self, since: datetime) -> float:
        """Get average processing time since given datetime."""
        times = []
        for date, values in self.processing_times.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                times.extend(values)
        return sum(times) / len(times) if times else 0.0
        
    def get_count(self, since: datetime) -> int:
        """Get total validations since given datetime."""
        return sum(
            count for date, count in self.validation_counts.items()
            if datetime.combine(date, datetime.min.time()) >= since
        )
        
    def get_success_rate(self, since: datetime) -> float:
        """Get validation success rate since given datetime."""
        total = 0
        success = 0
        for date, count in self.validation_counts.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                total += count
                success += self.validation_success[date]
        return (success / total * 100) if total > 0 else 0.0
        
    def get_by_source(self, since: datetime) -> Dict[str, int]:
        """Get token counts by source since given datetime."""
        result = defaultdict(int)
        for date, sources in self.tokens_by_source.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                for source, count in sources.items():
                    result[source] += count
        return dict(result)

# Message Processing Metrics
class MessageProcessingMetrics:
    """Track message processing performance."""
    
    def __init__(self) -> None:
        self.message_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self.messages_by_group = defaultdict(lambda: defaultdict(int))
        
    def record_message(self, success: bool, group_id: int, timestamp: datetime = None) -> None:
        """Record processed message."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        date = timestamp.date()
        self.message_counts[date] += 1
        if success:
            self.success_counts[date] += 1
        self.messages_by_group[date][group_id] += 1
        
    def get_count(self, since: datetime) -> int:
        """Get total messages processed since given datetime."""
        return sum(
            count for date, count in self.message_counts.items()
            if datetime.combine(date, datetime.min.time()) >= since
        )
        
    def get_success_rate(self, since: datetime) -> float:
        """Get message processing success rate since given datetime."""
        total = 0
        success = 0
        for date, count in self.message_counts.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                total += count
                success += self.success_counts[date]
        return (success / total * 100) if total > 0 else 0.0
        
    def get_by_group(self, since: datetime) -> Dict[int, int]:
        """Get message counts by group since given datetime."""
        result = defaultdict(int)
        for date, groups in self.messages_by_group.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                for group_id, count in groups.items():
                    result[group_id] += count
        return dict(result)

# Alert Generation Metrics
class AlertGenerationMetrics:
    """Track alert generation performance."""
    
    def __init__(self) -> None:
        self.alert_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self.alerts_by_type = defaultdict(lambda: defaultdict(int))
        
    def record_alert(self, success: bool, alert_type: str, timestamp: datetime = None) -> None:
        """Record generated alert."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        date = timestamp.date()
        self.alert_counts[date] += 1
        if success:
            self.success_counts[date] += 1
        self.alerts_by_type[date][alert_type] += 1
        
    def get_count(self, since: datetime) -> int:
        """Get total alerts generated since given datetime."""
        return sum(
            count for date, count in self.alert_counts.items()
            if datetime.combine(date, datetime.min.time()) >= since
        )
        
    def get_success_rate(self, since: datetime) -> float:
        """Get alert generation success rate since given datetime."""
        total = 0
        success = 0
        for date, count in self.alert_counts.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                total += count
                success += self.success_counts[date]
        return (success / total * 100) if total > 0 else 0.0
        
    def get_by_type(self, since: datetime) -> Dict[str, int]:
        """Get alert counts by type since given datetime."""
        result = defaultdict(int)
        for date, types in self.alerts_by_type.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                for alert_type, count in types.items():
                    result[alert_type] += count
        return dict(result)

# API Request Metrics
class APIRequestMetrics:
    """Track API request performance."""
    
    def __init__(self) -> None:
        self.request_times = defaultdict(list)
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.requests_by_endpoint = defaultdict(lambda: defaultdict(int))
        
    def record_request(
        self,
        duration: float,
        endpoint: str,
        success: bool,
        timestamp: datetime = None
    ):
        """Record API request."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        date = timestamp.date()
        self.request_times[date].append(duration)
        self.request_counts[date] += 1
        if not success:
            self.error_counts[date] += 1
        self.requests_by_endpoint[date][endpoint] += 1
        
    def get_count(self, since: datetime) -> int:
        """Get total requests since given datetime."""
        return sum(
            count for date, count in self.request_counts.items()
            if datetime.combine(date, datetime.min.time()) >= since
        )
        
    def get_average(self, since: datetime) -> float:
        """Get average request latency since given datetime."""
        times = []
        for date, values in self.request_times.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                times.extend(values)
        return sum(times) / len(times) if times else 0.0
        
    def get_error_rate(self, since: datetime) -> float:
        """Get error rate since given datetime."""
        total = 0
        errors = 0
        for date, count in self.request_counts.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                total += count
                errors += self.error_counts[date]
        return (errors / total * 100) if total > 0 else 0.0
        
    def get_by_endpoint(self, since: datetime) -> Dict[str, int]:
        """Get request counts by endpoint since given datetime."""
        result = defaultdict(int)
        for date, endpoints in self.requests_by_endpoint.items():
            if datetime.combine(date, datetime.min.time()) >= since:
                for endpoint, count in endpoints.items():
                    result[endpoint] += count
        return dict(result)

# System Health Metrics
class BotHealthMetrics:
    """Track bot system health metrics."""
    
    def __init__(self) -> None:
        self.start_time = datetime.utcnow()
        self.last_message_time = None
        self.message_queue = 0
        self.active_connections = 0
        self.errors = defaultdict(int)
        
    def update_queue_size(self, size: int) -> None:
        """Update message queue size."""
        self.message_queue = size
        
    def update_connections(self, count: int) -> None:
        """Update active connection count."""
        self.active_connections = count
        
    def record_message(self) -> None:
        """Record message processing time."""
        self.last_message_time = datetime.utcnow()
        
    def record_error(self, error_type: str) -> None:
        """Record error occurrence."""
        self.errors[datetime.utcnow().date()] += 1
        
    def get_uptime(self) -> float:
        """Get bot uptime in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
        
    def get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        return psutil.Process(os.getpid()).memory_percent()
        
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.Process(os.getpid()).cpu_percent()
        
    def get_queue_size(self) -> int:
        """Get current message queue size."""
        return self.message_queue
        
    def get_error_rate(self) -> float:
        """Get error rate for current day."""
        today = datetime.utcnow().date()
        return self.errors[today]
        
    def get_last_message_time(self) -> Optional[datetime]:
        """Get timestamp of last processed message."""
        return self.last_message_time
        
    def get_active_connections(self) -> int:
        """Get number of active connections."""
        return self.active_connections

# Initialize metrics
TOKEN_PROCESSING_TIME = TokenProcessingMetrics()
MESSAGE_PROCESSING_COUNT = MessageProcessingMetrics()
TOKEN_VALIDATION_COUNT = TokenProcessingMetrics()

# Prometheus metrics for token validation
PROM_TOKEN_VALIDATIONS = None
try:
    # Try to get existing metric or create a new one
    existing = REGISTRY._names_to_collectors.get('token_validations_total')
    if existing:
        PROM_TOKEN_VALIDATIONS = existing
    else:
        PROM_TOKEN_VALIDATIONS = Counter(
            'token_validations_total',
            'Total number of token validations',
            ['status']
        )
except Exception as e:
    # Fallback to a new metric with a unique name
    PROM_TOKEN_VALIDATIONS = Counter(
        'sma_token_validations_total',
        'Total number of token validations',
        ['status']
    )

ALERT_GENERATION_COUNT = AlertGenerationMetrics()
API_REQUEST_LATENCY = APIRequestMetrics()
BOT_HEALTH_METRICS = BotHealthMetrics()

# Prometheus metrics
PROM_TOKEN_PROCESSING_TIME = Histogram(
    'token_processing_seconds',
    'Token processing duration in seconds'
)

PROM_MESSAGE_PROCESSING_TOTAL = Counter(
    'messages_processed_total',
    'Total number of messages processed',
    ['status', 'group']
)

PROM_ALERT_GENERATION_TOTAL = Counter(
    'alerts_generated_total',
    'Total number of alerts generated',
    ['type', 'status']
)

PROM_API_REQUEST_DURATION = None
try:
    # Try to get existing metric or create a new one
    existing = REGISTRY._names_to_collectors.get('api_request_duration_seconds')
    if existing:
        PROM_API_REQUEST_DURATION = existing
    else:
        PROM_API_REQUEST_DURATION = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['endpoint']
        )
except Exception as e:
    # Fallback to a new metric with a unique name
    PROM_API_REQUEST_DURATION = Histogram(
        'sma_api_request_duration_seconds',
        'API request duration in seconds',
        ['endpoint']
    )

PROM_BOT_HEALTH = None
try:
    # Try to get existing metric or create a new one
    existing = REGISTRY._names_to_collectors.get('bot_health')
    if existing:
        PROM_BOT_HEALTH = existing
    else:
        PROM_BOT_HEALTH = Gauge(
            'bot_health',
            'Bot health metrics',
            ['metric']
        )
except Exception as e:
    # Fallback to a new metric with a unique name
    PROM_BOT_HEALTH = Gauge(
        'sma_bot_health',
        'Bot health metrics',
        ['metric']
    )
