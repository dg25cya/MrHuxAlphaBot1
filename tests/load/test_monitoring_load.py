"""Load testing for monitoring system."""
import asyncio
import aiohttp
import random
from datetime import datetime
import argparse
from loguru import logger

class MonitoringLoadTest:
    def __init__(self, admin_url: str, prometheus_url: str, grafana_url: str):
        """Initialize load test parameters."""
        self.admin_url = admin_url
        self.prometheus_url = prometheus_url
        self.grafana_url = grafana_url
        self.session = None

    async def setup(self):
        """Setup test session."""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup test session."""
        if self.session:
            await self.session.close()

    async def simulate_metrics_push(self, rate: int):
        """Simulate metrics being pushed."""
        while True:
            try:
                # Generate random metrics
                metrics = {
                    'token_count': random.randint(1, 100),
                    'processing_time': random.uniform(0.1, 2.0),
                    'error_count': random.randint(0, 5),
                    'memory_usage': random.uniform(100, 1000)
                }
                
                await self.session.post(
                    f"{self.admin_url}/metrics",
                    json=metrics
                )
                
                await asyncio.sleep(1/rate)
                
            except Exception as e:
                logger.error(f"Error pushing metrics: {e}")
                await asyncio.sleep(1)

    async def simulate_queries(self, rate: int):
        """Simulate metric queries."""
        queries = [
            'token_processing_total',
            'error_rate',
            'memory_usage',
            'cpu_usage'
        ]
        
        while True:
            try:
                query = random.choice(queries)
                await self.session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': query}
                )
                
                await asyncio.sleep(1/rate)
                
            except Exception as e:
                logger.error(f"Error querying metrics: {e}")
                await asyncio.sleep(1)

    async def simulate_dashboard_views(self, rate: int):
        """Simulate Grafana dashboard views."""
        dashboards = [
            'monitoring-overview',
            'alerts-dashboard',
            'resource-usage',
            'token-metrics'
        ]
        
        while True:
            try:
                dashboard = random.choice(dashboards)
                await self.session.get(
                    f"{self.grafana_url}/d/{dashboard}"
                )
                
                await asyncio.sleep(1/rate)
                
            except Exception as e:
                logger.error(f"Error viewing dashboard: {e}")
                await asyncio.sleep(1)

    async def run_load_test(self, duration: int, push_rate: int, query_rate: int, view_rate: int):
        """Run the load test."""
        logger.info("Starting load test...")
        
        await self.setup()
        
        try:
            tasks = [
                self.simulate_metrics_push(push_rate),
                self.simulate_queries(query_rate),
                self.simulate_dashboard_views(view_rate)
            ]
            
            await asyncio.wait(
                tasks,
                timeout=duration
            )
            
        finally:
            await self.cleanup()

async def main():
    parser = argparse.ArgumentParser(description='Run monitoring load tests')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--push-rate', type=int, default=10, help='Metrics push rate per second')
    parser.add_argument('--query-rate', type=int, default=5, help='Query rate per second')
    parser.add_argument('--view-rate', type=int, default=2, help='Dashboard view rate per second')
    parser.add_argument('--admin-url', default='http://localhost:8001', help='Admin API URL')
    parser.add_argument('--prometheus-url', default='http://localhost:9090', help='Prometheus URL')
    parser.add_argument('--grafana-url', default='http://localhost:3000', help='Grafana URL')
    
    args = parser.parse_args()
    
    load_test = MonitoringLoadTest(
        args.admin_url,
        args.prometheus_url,
        args.grafana_url
    )
    
    await load_test.run_load_test(
        args.duration,
        args.push_rate,
        args.query_rate,
        args.view_rate
    )

if __name__ == '__main__':
    asyncio.run(main())
