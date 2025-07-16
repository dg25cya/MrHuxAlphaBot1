import asyncio
from loguru import logger
from typing import Optional

class ContinuousPlayHunter:
    """Always-on play hunting engine for all sources."""
    def __init__(self, source_manager, output_service):
        self.source_manager = source_manager
        self.output_service = output_service
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        if not self.source_manager or not self.output_service:
            logger.warning("ContinuousPlayHunter: source_manager or output_service not set. Cannot start.")
            return
        self._running = True
        logger.info("ContinuousPlayHunter: Starting continuous hunting...")
        self._task = asyncio.create_task(self._hunt_loop())

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ContinuousPlayHunter: Stopped continuous hunting.")

    async def status(self):
        return {
            "running": self._running,
            # Add more status info as needed
        }

    async def _hunt_loop(self):
        while self._running:
            try:
                logger.info("ContinuousPlayHunter: Scanning all sources...")
                await self.source_manager.scan_all_sources(output_service=self.output_service)
                await asyncio.sleep(60)  # Scan every 60 seconds (adjust as needed)
            except Exception as e:
                logger.error(f"ContinuousPlayHunter: Error in hunting loop: {e}")
                await asyncio.sleep(10)

# Singleton instance for import
# Note: This may be a ContinuousPlayHunter or DummyHunter
hunter_instance = None

def get_play_hunter(source_manager=None, output_service=None):
    global hunter_instance
    if hunter_instance is None:
        if source_manager and output_service:
            hunter_instance = ContinuousPlayHunter(source_manager, output_service)
        else:
            # Create a dummy instance that logs warnings
            class DummyHunter:
                async def start(self):
                    logger.warning("DummyHunter: Cannot start hunting, dependencies missing.")
                async def stop(self):
                    logger.warning("DummyHunter: Cannot stop hunting, dependencies missing.")
                async def status(self):
                    return {"running": False, "error": "Dependencies missing"}
            hunter_instance = DummyHunter()
    return hunter_instance
