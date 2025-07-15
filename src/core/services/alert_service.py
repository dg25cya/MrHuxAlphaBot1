"""Service for handling token alerts."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.models.alert import Alert, AlertType, AlertPriority
from src.models.token import Token
from src.models.token_metrics import TokenMetrics
from src.models.token_score import TokenScore
from src.utils.decimal import decimal_abs, decimal_to_percent
from src.utils.exceptions import AlertServiceError

settings = get_settings()


class AlertService:
    """Service for managing token alerts."""
    
    def __init__(self, db: Session) -> None:
        """Initialize alert service."""
        self.db = db

    async def check_alerts(self, token_id: int) -> List[Alert]:
        """Check alerts for a token."""
        try:
            # Get token
            token = self.db.query(Token).filter(Token.id == token_id).first()
            if not token:
                return []

            # Get latest metrics
            metrics = (self.db.query(TokenMetrics)
                      .filter(TokenMetrics.token_id == token_id)
                      .order_by(TokenMetrics.created_at.desc())
                      .first())
            if not metrics:
                return []

            alerts = []

            # Price alert check
            price_change = Decimal(str(metrics.price_change_24h or 0))
            if abs(price_change) >= settings.price_alert_threshold:
                alerts.append(Alert(
                    token_id=token_id,
                    alert_type=AlertType.PRICE,
                    priority=AlertPriority.HIGH if abs(price_change) >= 50 else AlertPriority.MEDIUM,
                    message=f"Price changed by {decimal_to_percent(price_change)}%"
                ))

            # Volume alert check
            if metrics.volume_24h:
                prev_metrics = (self.db.query(TokenMetrics)
                              .filter(TokenMetrics.token_id == token_id)
                              .filter(TokenMetrics.created_at < metrics.created_at)
                              .order_by(TokenMetrics.created_at.desc())
                              .first())

                if prev_metrics and prev_metrics.volume_24h:
                    volume_change = Decimal(str(metrics.volume_24h)) / Decimal(str(prev_metrics.volume_24h or 1)) - 1
                    if abs(volume_change) >= settings.volume_alert_threshold:
                        alerts.append(Alert(
                            token_id=token_id,
                            alert_type=AlertType.VOLUME,
                            priority=AlertPriority.HIGH if abs(volume_change) >= 2 else AlertPriority.MEDIUM,
                            message=f"Volume changed by {decimal_to_percent(volume_change)}%"
                        ))

            # Holder alert check
            if metrics.holder_count is not None:
                prev_metrics = (self.db.query(TokenMetrics)
                              .filter(TokenMetrics.token_id == token_id)
                              .filter(TokenMetrics.created_at < metrics.created_at)
                              .order_by(TokenMetrics.created_at.desc())
                              .first())

                if prev_metrics and prev_metrics.holder_count:
                    holder_change = (metrics.holder_count - prev_metrics.holder_count) / prev_metrics.holder_count
                    if abs(holder_change) >= settings.holder_alert_threshold:
                        alerts.append(Alert(
                            token_id=token_id,
                            alert_type=AlertType.HOLDERS,
                            priority=AlertPriority.MEDIUM,
                            message=f"Holder count changed by {int(holder_change * 100)}%"
                        ))

            # Score alert check
            score = (self.db.query(TokenScore)
                    .filter(TokenScore.token_id == token_id)
                    .order_by(TokenScore.created_at.desc())
                    .first())

            if score:
                prev_score = (self.db.query(TokenScore)
                            .filter(TokenScore.token_id == token_id)
                            .filter(TokenScore.created_at < score.created_at)
                            .order_by(TokenScore.created_at.desc())
                            .first())

                if prev_score:
                    # Convert score values to Python floats for comparison
                    safety_change = float(score.safety_score) - float(prev_score.safety_score)
                    total_change = float(score.total_score) - float(prev_score.total_score)

                    if abs(safety_change) >= 20 or abs(total_change) >= 20:
                        alerts.append(Alert(
                            token_id=token_id,
                            alert_type=AlertType.SECURITY,
                            priority=AlertPriority.HIGH if safety_change < 0 or total_change < 0 else AlertPriority.MEDIUM,
                            message=f"Security score changed significantly: Safety {int(safety_change)} points, Total {int(total_change)} points"
                        ))

            return alerts

        except Exception as e:
            logger.exception(f"Error checking alerts for token {token_id}: {e}")
            raise AlertServiceError(f"Alert check failed: {str(e)}")

    async def cleanup_old_alerts(self, days: int = 30) -> int:
        """Clean up alerts older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = self.db.query(Alert).filter(
                Alert.created_at < cutoff_date
            ).delete()
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old alerts")
            return deleted_count
        except Exception as e:
            logger.exception(f"Error cleaning up old alerts: {e}")
            self.db.rollback()
            raise AlertServiceError(f"Alert cleanup failed: {str(e)}")

    def get_verdict(self, alerts: List[Alert]) -> str:
        """Get overall verdict based on alerts."""
        if not alerts:
            return "CLEAR"
        
        high_priority = [a for a in alerts if a.priority == AlertPriority.HIGH]
        if high_priority:
            return "HIGH_RISK"
        
        medium_priority = [a for a in alerts if a.priority == AlertPriority.MEDIUM]
        if medium_priority:
            return "MEDIUM_RISK"
        
        return "LOW_RISK"


# Convenience functions for backward compatibility
async def check_token_alerts(token_id: int, db: Session) -> List[Alert]:
    """Check alerts for a token."""
    service = AlertService(db)
    return await service.check_alerts(token_id)


async def cleanup_old_alerts(db: Session, days: int = 30) -> int:
    """Clean up old alerts."""
    service = AlertService(db)
    return await service.cleanup_old_alerts(days)


def get_verdict(alerts: List[Alert]) -> str:
    """Get verdict from alerts."""
    service = AlertService(None)  # We don't need db for this function
    return service.get_verdict(alerts)
