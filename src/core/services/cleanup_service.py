"""Data cleanup service for managing old data and maintenance tasks."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger
from sqlalchemy import and_, func, or_

from src.models.token import Token
from src.models.mention import TokenMention
from src.models.alert import Alert
from src.models.monitored_source import MonitoredSource
from src.utils.db import db_session

class CleanupService:
    """Service for cleaning up old data and performing maintenance tasks."""
    
    def __init__(self) -> None:
        """Initialize cleanup service."""
        self.last_cleanup = None
        self.cleanup_stats = {}
    
    async def cleanup_old_data(
        self,
        days: int = 30,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Clean up old data older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = {
            "tokens_removed": 0,
            "mentions_removed": 0,
            "alerts_removed": 0,
            "sources_cleaned": 0,
            "cutoff_date": cutoff_date.isoformat(),
            "dry_run": dry_run
        }
        
        try:
            with db_session() as db:
                # Clean up old token mentions
                if not dry_run:
                    mentions_deleted = db.query(TokenMention).filter(
                        TokenMention.mentioned_at < cutoff_date
                    ).delete()
                    stats["mentions_removed"] = mentions_deleted
                else:
                    mentions_count = db.query(TokenMention).filter(
                        TokenMention.mentioned_at < cutoff_date
                    ).count()
                    stats["mentions_removed"] = mentions_count
                
                # Clean up old alerts
                if not dry_run:
                    alerts_deleted = db.query(Alert).filter(
                        Alert.created_at < cutoff_date
                    ).delete()
                    stats["alerts_removed"] = alerts_deleted
                else:
                    alerts_count = db.query(Alert).filter(
                        Alert.created_at < cutoff_date
                    ).count()
                    stats["alerts_removed"] = alerts_count
                
                # Clean up old tokens (keep some recent ones)
                if not dry_run:
                    # Keep tokens that have been updated recently or have high scores
                    tokens_to_keep = db.query(Token).filter(
                        or_(
                            Token.last_updated_at > cutoff_date,
                            Token.score > 0.5
                        )
                    ).subquery()
                    
                    tokens_deleted = db.query(Token).filter(
                        and_(
                            Token.last_updated_at < cutoff_date,
                            Token.score <= 0.5,
                            ~Token.id.in_(tokens_to_keep.select())
                        )
                    ).delete()
                    stats["tokens_removed"] = tokens_deleted
                else:
                    tokens_count = db.query(Token).filter(
                        and_(
                            Token.last_updated_at < cutoff_date,
                            Token.score <= 0.5
                        )
                    ).count()
                    stats["tokens_removed"] = tokens_count
                
                # Clean up source error logs
                if not dry_run:
                    sources_updated = db.query(MonitoredSource).filter(
                        MonitoredSource.last_error.isnot(None)
                    ).update({
                        "last_error": None,
                        "error_count": 0
                    })
                    stats["sources_cleaned"] = sources_updated
                
                if not dry_run:
                    db.commit()
                    logger.info(f"Cleanup completed: {stats}")
                else:
                    logger.info(f"Cleanup dry run completed: {stats}")
                
                self.last_cleanup = datetime.utcnow()
                self.cleanup_stats = stats
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            if not dry_run:
                db.rollback()
            stats["error"] = str(e)
        
        return stats
    
    async def run_cleanup(self, days: int = 30) -> Dict[str, Any]:
        """Run the actual cleanup operation."""
        return await self.cleanup_old_data(days=days, dry_run=False)
    
    async def dry_run_cleanup(self, days: int = 30) -> Dict[str, Any]:
        """Run a dry run cleanup to see what would be deleted."""
        return await self.cleanup_old_data(days=days, dry_run=True)
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get the last cleanup statistics."""
        return {
            "last_cleanup": self.last_cleanup.isoformat() if self.last_cleanup else None,
            "stats": self.cleanup_stats
        }

# Global cleanup service instance
cleanup_service = CleanupService() 