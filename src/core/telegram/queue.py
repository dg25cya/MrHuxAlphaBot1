"""Message queue and rate limiting for Telegram messages."""
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
from loguru import logger

class MessageRateLimiter:
    """Rate limiter for message processing."""
    
    def __init__(self, rate_limit: int = 60, window: int = 60) -> None:
        """
        Initialize rate limiter.
        
        Args:
            rate_limit: Maximum number of messages per window
            window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.window = window
        self.counts = defaultdict(list)
        
    def _clean_old_timestamps(self, group_id: int) -> None:
        """Remove timestamps older than the window."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window)
        
        self.counts[group_id] = [
            ts for ts in self.counts[group_id]
            if ts > window_start
        ]
        
    def can_process(self, group_id: int) -> bool:
        """Check if a message from the group can be processed."""
        self._clean_old_timestamps(group_id)
        return len(self.counts[group_id]) < self.rate_limit
        
    def add_message(self, group_id: int) -> None:
        """Record a message processing attempt."""
        self.counts[group_id].append(datetime.utcnow())

class MessageQueue:
    """Async message queue with rate limiting and priority."""
    
    def __init__(
        self,
        rate_limiter: Optional[MessageRateLimiter] = None,
        max_size: int = 1000
    ):
        self.queue = asyncio.PriorityQueue(maxsize=max_size)
        self.rate_limiter = rate_limiter or MessageRateLimiter()
        self.processing = False
        
    async def put(
        self,
        group_id: int,
        message: Dict[str, Any],
        priority: int = 1
    ):
        """
        Add message to queue.
        
        Args:
            group_id: Telegram group ID
            message: Message data
            priority: Priority level (lower number = higher priority)
        """
        # Add timestamp for ordering within same priority
        timestamp = datetime.utcnow().timestamp()
        
        await self.queue.put((
            priority,
            timestamp,
            {
                "group_id": group_id,
                "data": message
            }
        ))
        
    async def process_messages(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        error_handler: Optional[Callable[[Exception], Awaitable[None]]] = None
    ):
        """
        Start processing messages from queue.
        
        Args:
            handler: Async function to handle each message
            error_handler: Optional async function to handle errors
        """
        self.processing = True
        
        try:
            while self.processing:
                # Get next message
                priority, timestamp, message = await self.queue.get()
                group_id = message["group_id"]
                
                # Check rate limit
                if not self.rate_limiter.can_process(group_id):
                    # Re-queue with lower priority after delay
                    await asyncio.sleep(1)
                    await self.put(group_id, message["data"], priority + 1)
                    continue
                    
                try:
                    # Process message
                    self.rate_limiter.add_message(group_id)
                    await handler(message["data"])
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    if error_handler:
                        try:
                            await error_handler(e)
                        except Exception as eh_error:
                            logger.error(f"Error in error handler: {str(eh_error)}")
                            
                finally:
                    # Mark task as done
                    self.queue.task_done()
                    
        except asyncio.CancelledError:
            self.processing = False
            
    def stop(self) -> None:
        """Stop message processing."""
        self.processing = False
