"""Service for managing monitored sources."""
from typing import List, Dict, Any, Optional
import asyncio

from loguru import logger
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.models.monitored_source import MonitoredSource

settings = get_settings()


class SourceManager:
    """Manager for monitored sources."""

    def __init__(self, db: Session) -> None:
        """Initialize source manager."""
        self.db = db
        self._running = False
        self._scan_tasks: Dict[int, asyncio.Task] = {}

    async def start(self):
        """Start monitoring all active sources."""
        self._running = True
        try:
            sources = (self.db.query(MonitoredSource)
                      .filter(MonitoredSource.is_active == True)
                      .all())
            for source in sources:
                await self.start_monitoring(source)

        except Exception as e:
            logger.error(f"Error starting source manager: {e}")
            raise

    async def stop(self):
        """Stop monitoring all sources."""
        self._running = False
        for task in self._scan_tasks.values():
            task.cancel()

        # Wait for all tasks to finish
        if self._scan_tasks:
            await asyncio.gather(*self._scan_tasks.values(), return_exceptions=True)

        self._scan_tasks.clear()

    async def start_monitoring(self, source: MonitoredSource):
        """Start monitoring a single source."""
        if source.id in self._scan_tasks:
            logger.warning(f"Source {source.id} is already being monitored")
            return

        task = asyncio.create_task(self._scan_source(source))
        self._scan_tasks[source.id] = task

    async def stop_monitoring(self, source_id: int):
        """Stop monitoring a single source."""
        if source_id in self._scan_tasks:
            self._scan_tasks[source_id].cancel()
            await self._scan_tasks[source_id]
            del self._scan_tasks[source_id]

    async def _scan_source(self, source: MonitoredSource):
        """Continuously scan a source at its configured interval."""
        while self._running:
            try:
                # Implement source scanning logic here
                await asyncio.sleep(source.scan_interval)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error scanning source {source.id}: {e}")
                await asyncio.sleep(settings.error_cooldown)

        logger.info(f"Stopped monitoring source {source.id}")