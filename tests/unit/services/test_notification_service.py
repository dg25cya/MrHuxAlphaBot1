"""Unit tests for the notification service."""
import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.services.notify import (
    AlertNotification,
    AlertSeverity,
    AlertType,
    AlertSource,
    NotificationService
)

@pytest.fixture
def mock_settings():
    """Mock settings with notification configuration."""
    with patch("src.core.services.notify.settings") as mock_settings:
        mock_settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
        mock_settings.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/test"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "test@test.com"
        mock_settings.SMTP_PASSWORD = "testpass"
        mock_settings.EMAIL_FROM = "from@test.com"
        mock_settings.EMAIL_TO = "to@test.com"
        mock_settings.EMAIL_USE_TLS = True
        mock_settings.PAGERDUTY_API_KEY = "test_pd_key"
        mock_settings.PAGERDUTY_SERVICE_ID = "test_pd_service"
        yield mock_settings

@pytest.fixture
def notification_service(mock_settings):
    """Create a notification service instance with mocked settings."""
    service = NotificationService()
    service._http_client = AsyncMock()
    service.pd_session = MagicMock()
    return service

@pytest.fixture
def sample_alert():
    """Create a sample alert notification."""
    return AlertNotification(
        title="Test Alert",
        message="This is a test alert",
        severity=AlertSeverity.WARNING,
        alert_type=AlertType.PRICE_MOVE,
        source=AlertSource.PRICE_MONITOR,
        token_address="So11111111111111111111111111111111111111112",
        token_symbol="SOL",
        mention_count=5,
        metrics_snapshot={
            "price_change_1h": 10.5,
            "volume_24h": 1000000
        },
        details={
            "additional": "test detail"
        }
    )

@pytest.mark.asyncio
async def test_send_slack_notification_success(notification_service, sample_alert):
    """Test successful Slack notification."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    notification_service._http_client.post.return_value = mock_response

    success = await notification_service.send_slack_notification(sample_alert)

    assert success is True
    notification_service._http_client.post.assert_called_once()
    called_url = notification_service._http_client.post.call_args[0][0]
    assert called_url == notification_service.slack_webhook_url

@pytest.mark.asyncio
async def test_send_discord_notification_success(notification_service, sample_alert):
    """Test successful Discord notification."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    notification_service._http_client.post.return_value = mock_response

    success = await notification_service.send_discord_notification(sample_alert)

    assert success is True
    notification_service._http_client.post.assert_called_once()
    called_url = notification_service._http_client.post.call_args[0][0]
    assert called_url == notification_service.discord_webhook_url

@pytest.mark.asyncio
async def test_rate_limit_handling(notification_service, sample_alert):
    """Test rate limit handling."""
    # Mock rate limiter to simulate reaching the limit
    notification_service.slack_limiter.acquire = AsyncMock(side_effect=Exception("Rate limit exceeded"))
    
    success = await notification_service._acquire_rate_limit(
        notification_service.slack_limiter,
        notification_service.SLACK_SERVICE_ID,
        "slack"
    )
    
    assert success is False

@pytest.mark.asyncio
async def test_retry_logic(notification_service, sample_alert):
    """Test notification retry logic."""
    # Mock HTTP client to fail first then succeed
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    notification_service._http_client.post = AsyncMock(
        side_effect=[Exception("Network error"), mock_response]
    )

    success = await notification_service.send_notification(sample_alert)

    assert success is True
    assert notification_service._http_client.post.call_count == 2

@pytest.mark.asyncio
async def test_pagerduty_notification_critical(notification_service, sample_alert):
    """Test PagerDuty notification for critical alerts."""
    # Update alert to critical severity
    sample_alert.severity = AlertSeverity.CRITICAL
    
    # Mock PagerDuty response
    notification_service.pd_session.rpost.return_value = {"id": "test_incident_id"}
    
    success = await notification_service.send_pagerduty_notification(sample_alert)
    
    assert success is True
    notification_service.pd_session.rpost.assert_called_once()

@pytest.mark.asyncio
async def test_queue_failed_notification(notification_service, sample_alert):
    """Test queuing of failed notifications."""
    with patch("src.core.services.notify.MessageQueueManager") as mock_queue:
        mock_queue.queue_message = AsyncMock()
        
        await notification_service._queue_failed_notification(sample_alert)
        
        mock_queue.queue_message.assert_called_once()
        queue_name = mock_queue.queue_message.call_args[0][0]
        assert queue_name == "failed_notifications"

@pytest.mark.asyncio
async def test_cleanup_old_notifications(notification_service):
    """Test cleanup of old notifications."""
    with patch("src.core.services.notify.MessageQueueManager") as mock_queue:
        mock_queue.get_missed_messages = AsyncMock(return_value=[
            {
                "id": "test_id",
                "retry_count": 3,
                "next_retry": datetime.now(timezone.utc).isoformat()
            }
        ])
        mock_queue.delete_message = AsyncMock()
        
        await notification_service.cleanup_old_notifications()
        
        mock_queue.delete_message.assert_called_once()

def test_severity_emoji():
    """Test emoji generation for different severities."""
    assert AlertNotification.get_severity_emoji(AlertSeverity.CRITICAL) == "🚨"
    assert AlertNotification.get_severity_emoji(AlertSeverity.WARNING) == "⚠️"
    assert AlertNotification.get_severity_emoji(AlertSeverity.INFO) == "ℹ️"

def test_format_metrics():
    """Test metrics formatting."""
    metrics = {
        "value": 1500000,
        "small_value": 850.75,
        "text": "test"
    }
    
    # Test without markdown
    formatted = NotificationService._format_metrics(None, metrics)
    assert "$1.50M" in formatted
    assert "$850.75" in formatted
    
    # Test with markdown
    formatted_md = NotificationService._format_metrics(None, metrics, use_markdown=True)
    assert "**Value**: $1.50M" in formatted_md
