"""Admin metrics for monitoring dashboard and user actions."""
from prometheus_client import Counter, Histogram, Gauge

# Dashboard metrics
dashboard_views = Counter(
    'dashboard_views_total',
    'Number of dashboard views',
    ['dashboard']
)

# User action metrics
user_actions = Counter(
    'user_actions_total',
    'Number of user actions performed',
    ['action']
)

# Session metrics
session_duration = Histogram(
    'session_duration_seconds',
    'Duration of user sessions',
    ['user_type']
)

# Resource usage metrics
resource_usage = Gauge(
    'resource_usage',
    'Current resource usage',
    ['resource']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Cache metrics
cache_operations = Counter(
    'cache_operations_total',
    'Number of cache operations',
    ['operation']
)

# Token operation metrics
token_operations = Counter(
    'token_operations_total',
    'Number of token operations',
    ['operation']
)

# Authentication metrics
auth_failures = Counter(
    'auth_failures_total',
    'Number of authentication failures',
    ['reason']
)

# Background task metrics
background_tasks = Histogram(
    'background_task_duration_seconds',
    'Background task duration',
    ['task']
)
