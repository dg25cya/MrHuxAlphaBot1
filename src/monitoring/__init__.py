"""Monitoring module for consistent metric collection."""
from src.monitoring.client import get_monitoring_client, MetricType, Metric

__all__ = ['get_monitoring_client', 'MetricType', 'Metric']
