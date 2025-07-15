"""Integration tests for monitoring system."""
import pytest
import pytest_asyncio
import aiohttp
import asyncio
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry

class TestMonitoringIntegration:
    @pytest_asyncio.fixture
    async def monitoring_session(self):
        """Create a test session."""
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.mark.asyncio
    async def test_metrics_flow(self, monitoring_session):
        """Test complete metrics collection flow."""
        # Generate test metrics
        test_metrics = {
            'token_processing': 100,
            'processing_time': 0.5,
            'error_count': 2,
            'memory_usage': 512.0
        }
        
        # Push metrics
        async with monitoring_session.post(
            'http://localhost:9091/metrics/job/test',
            json=test_metrics
        ) as response:
            assert response.status == 200
            
        # Query metrics
        async with monitoring_session.get(
            'http://localhost:9090/api/v1/query',
            params={'query': 'token_processing_total'}
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data['status'] == 'success'
            assert float(data['data']['result'][0]['value'][1]) == 100

    @pytest.mark.asyncio
    async def test_alert_flow(self, monitoring_session):
        """Test alert generation and notification flow."""
        # Trigger test alert
        async with monitoring_session.post(
            'http://localhost:9093/api/v2/alerts',
            json=[{
                'labels': {
                    'alertname': 'TestAlert',
                    'severity': 'critical'
                },
                'annotations': {
                    'summary': 'Test alert summary',
                    'description': 'Test alert description'
                },
                'startsAt': datetime.utcnow().isoformat() + 'Z'
            }]
        ) as response:
            assert response.status == 200
            
        # Check alert status
        async with monitoring_session.get(
            'http://localhost:9093/api/v2/alerts'
        ) as response:
            assert response.status == 200
            alerts = await response.json()
            assert any(a['labels']['alertname'] == 'TestAlert' for a in alerts)

    @pytest.mark.asyncio
    async def test_cleanup_flow(self, monitoring_session):
        """Test monitoring data cleanup flow."""
        # Push old test data
        old_time = int((datetime.utcnow() - timedelta(days=8)).timestamp() * 1000)
        test_data = {
            'name': 'test_metric',
            'timestamp': old_time,
            'value': 1.0
        }
        
        async with monitoring_session.post(
            'http://localhost:9091/metrics/job/old_test',
            json=test_data
        ) as response:
            assert response.status == 200
            
        # Trigger cleanup
        async with monitoring_session.post(
            'http://localhost:8001/api/v1/monitoring/cleanup',
            json={'days': 7}
        ) as response:
            assert response.status == 200
            result = await response.json()
            assert result['cleaned'] > 0
            
        # Verify data is cleaned up
        async with monitoring_session.get(
            'http://localhost:9090/api/v1/query',
            params={
                'query': 'test_metric',
                'time': old_time / 1000
            }
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert not data['data']['result']

    @pytest.mark.asyncio
    async def test_grafana_dashboard_flow(self, monitoring_session):
        """Test Grafana dashboard data flow."""
        # Query dashboard data
        async with monitoring_session.get(
            'http://localhost:3000/api/dashboards/uid/monitoring',
            headers={'Authorization': 'Bearer test-token'}
        ) as response:
            assert response.status == 200
            dashboard = await response.json()
            assert dashboard['dashboard']['title'] == 'Monitoring Overview'
            
        # Check metrics used in dashboard
        for panel in dashboard['dashboard']['panels']:
            if 'targets' in panel:
                for target in panel['targets']:
                    query = target['expr']
                    async with monitoring_session.get(
                        'http://localhost:9090/api/v1/query',
                        params={'query': query}
                    ) as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data['status'] == 'success'
