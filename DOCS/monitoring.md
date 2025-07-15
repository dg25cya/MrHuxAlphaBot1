# Monitoring Infrastructure

## Overview
The Mr Hux Alpha Bot uses a comprehensive monitoring stack consisting of:
- Prometheus for metrics collection
- Alertmanager for notifications
- Grafana for visualization
- Node Exporter for system metrics
- cAdvisor for container metrics

## Metrics Collected

### Application Metrics
- Token processing time
- API request rates
- Success/failure rates
- Queue lengths
- Processing latency

### System Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

### Business Metrics
- Tokens processed
- Alert counts
- Group activity
- Token scores

## Alerting Rules

### Critical Alerts
- High error rates (>10% in 5m)
- Service down
- Memory usage >90%
- Database connection failures

### Warning Alerts
- High latency (>10s)
- High API usage
- Low disk space
- Increased error rates

## Dashboards

### Main Dashboards
1. System Overview
   - System resources
   - Container health
   - Key metrics summary

2. Token Monitoring
   - Processing metrics
   - Score distribution
   - Success rates

3. Risk Monitoring
   - Error rates
   - Latency spikes
   - Resource bottlenecks

## Maintenance

### Daily Tasks
- Check alert status
- Review error logs
- Monitor resource usage

### Weekly Tasks
- Review dashboard trends
- Check alert configurations
- Verify backup metrics

### Monthly Tasks
- Clean old metrics
- Update alert thresholds
- Performance review

## Setup Instructions

1. Start monitoring stack:
```bash
python scripts/setup_monitoring.py
```

2. Verify health:
```powershell
./scripts/run_monitoring_health.ps1
```

3. Access dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

## Configuration Files

### Prometheus
Location: `docker/prometheus/prometheus.yml`
- Scrape configs
- Alert rules
- Job definitions

### Alertmanager
Location: `docker/alertmanager/alertmanager.yml`
- Notification routing
- Email/Slack integration
- Alert grouping

### Grafana
Location: `docker/grafana/`
- Dashboard provisioning
- Data sources
- Alert settings

## Troubleshooting

### Common Issues
1. Missing metrics
   - Check service connectivity
   - Verify scrape configs
   - Check service logs

2. Alert notification failures
   - Check SMTP settings
   - Verify webhook URLs
   - Check network connectivity

3. Dashboard issues
   - Clear browser cache
   - Check data source status
   - Verify permissions

### Health Checks
Run the monitoring health script:
```powershell
./scripts/run_monitoring_health.ps1
```

### Log Locations
- Application: `logs/mr_hux_alpha_bot.log`
- Prometheus: `logs/prometheus.log`
- Alertmanager: `logs/alertmanager.log`
- Grafana: `logs/grafana.log`

## Backup and Recovery

### Backup Procedures
1. Grafana dashboards:
```bash
python scripts/backup_grafana.py
```

2. Prometheus data:
```bash
python scripts/backup_monitoring.py
```

### Recovery Steps
1. Restore configuration files
2. Import dashboard backups
3. Verify metric collection
4. Test alert notifications