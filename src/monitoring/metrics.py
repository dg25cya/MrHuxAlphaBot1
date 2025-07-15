"""Standard metrics definition."""
from src.monitoring.client import get_monitoring_client, MetricType

# Token processing metrics
token_processing_counter = get_monitoring_client().create_metric(
    "sma_token_processing_total",
    "Total number of tokens processed",
    MetricType.COUNTER,
    ["status"]
)

token_processing_time = get_monitoring_client().create_metric(
    "sma_token_processing_seconds",
    "Time taken to process tokens",
    MetricType.HISTOGRAM,
    ["operation"]
)

token_queue_size = get_monitoring_client().create_metric(
    "sma_token_queue_size",
    "Current size of the token processing queue",
    MetricType.GAUGE
)

# API metrics
api_request_counter = get_monitoring_client().create_metric(
    "sma_api_requests_total",
    "Total number of API requests",
    MetricType.COUNTER,
    ["endpoint", "method", "status"]
)

api_request_duration = get_monitoring_client().create_metric(
    "sma_api_request_duration_seconds",
    "API request duration in seconds",
    MetricType.HISTOGRAM,
    ["endpoint"]
)

# Database metrics
db_operation_duration = get_monitoring_client().create_metric(
    "sma_db_operation_duration_seconds",
    "Database operation duration in seconds",
    MetricType.HISTOGRAM,
    ["operation", "table"]
)

db_connection_pool = get_monitoring_client().create_metric(
    "sma_db_connection_pool_size",
    "Current size of the database connection pool",
    MetricType.GAUGE
)

# Resource metrics
memory_usage = get_monitoring_client().create_metric(
    "sma_memory_usage_bytes",
    "Current memory usage in bytes",
    MetricType.GAUGE,
    ["type"]
)

message_processing_queue = get_monitoring_client().create_metric(
    "sma_message_queue_size",
    "Current size of the message processing queue",
    MetricType.GAUGE
)

# Error metrics
error_counter = get_monitoring_client().create_metric(
    "sma_errors_total",
    "Total number of errors",
    MetricType.COUNTER,
    ["type", "source"]
)

retry_counter = get_monitoring_client().create_metric(
    "sma_retries_total",
    "Total number of operation retries",
    MetricType.COUNTER,
    ["operation"]
)

# Cache metrics
cache_hit_counter = get_monitoring_client().create_metric(
    "sma_cache_hits_total",
    "Total number of cache hits",
    MetricType.COUNTER,
    ["cache"]
)

cache_miss_counter = get_monitoring_client().create_metric(
    "sma_cache_misses_total",
    "Total number of cache misses",
    MetricType.COUNTER,
    ["cache"]
)

# Business metrics
token_score_distribution = get_monitoring_client().create_metric(
    "sma_token_score_distribution",
    "Distribution of token scores",
    MetricType.HISTOGRAM,
    ["type"]
)

alert_counter = get_monitoring_client().create_metric(
    "sma_alerts_total",
    "Total number of alerts generated",
    MetricType.COUNTER,
    ["type", "severity"]
)
