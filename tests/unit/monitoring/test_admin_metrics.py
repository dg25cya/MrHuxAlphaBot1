"""Unit tests for admin metrics monitoring."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from prometheus_client import CollectorRegistry
from src.monitoring.admin_metrics import (
    dashboard_views, 
    user_actions,
    session_duration,
    resource_usage,
    db_query_duration,
    cache_operations,
    token_operations,
    auth_failures,
    background_tasks
)

class TestAdminMetrics:
    @pytest.fixture
    def registry(self):
        return CollectorRegistry()
        
    def test_dashboard_metrics(self, registry):
        """Test dashboard view metrics collection."""
        dashboard_views.labels(dashboard="token_overview").inc()
        dashboard_views.labels(dashboard="alert_manager").inc(2)
        
        assert dashboard_views._value.get() == 3
        
    def test_user_action_metrics(self, registry):
        """Test user action metrics collection."""
        user_actions.labels(action="clear_alerts").inc()
        user_actions.labels(action="modify_settings").inc(2)
        
        assert user_actions._value.get() == 3
        
    @pytest.mark.asyncio
    async def test_session_tracking(self, registry):
        """Test session duration tracking."""
        with session_duration.labels(user_type="admin").time():
            await asyncio.sleep(0.1)
            
        assert session_duration._value.get() > 0
        
    def test_resource_metrics(self, registry):
        """Test resource usage metrics."""
        resource_usage.labels(resource="cpu").set(45.2)
        resource_usage.labels(resource="memory").set(1024.5)
        
        assert resource_usage.labels(resource="cpu")._value.get() == 45.2
        assert resource_usage.labels(resource="memory")._value.get() == 1024.5
        
    @pytest.mark.asyncio 
    async def test_db_query_metrics(self, registry):
        """Test database query metrics."""
        with db_query_duration.labels(operation="select").time():
            await asyncio.sleep(0.1)
            
        assert db_query_duration._value.get() > 0
        
    def test_token_operation_metrics(self, registry):
        """Test token operation metrics."""
        token_operations.labels(operation="validate").inc()
        token_operations.labels(operation="score").inc(2)
        
        assert token_operations._value.get() == 3
        
    def test_auth_metrics(self, registry):
        """Test authentication metrics."""
        auth_failures.labels(reason="invalid_token").inc()
        auth_failures.labels(reason="expired").inc(2)
        
        assert auth_failures._value.get() == 3
        
    def test_background_task_metrics(self, registry):
        """Test background task metrics."""
        with background_tasks.labels(task="cleanup").time():
            time.sleep(0.1)
            
        assert background_tasks._value.get() > 0

    def test_cache_operation_metrics(self, registry):
        """Test cache operation metrics."""
        cache_operations.labels(operation="hit").inc(5)
        cache_operations.labels(operation="miss").inc(2)
        
        assert cache_operations.labels(operation="hit")._value.get() == 5
        assert cache_operations.labels(operation="miss")._value.get() == 2
