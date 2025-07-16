"""Output channel service for handling message delivery."""
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Union, Any
import aiohttp
from loguru import logger
from sqlalchemy import Integer, cast, case, Column, update
from sqlalchemy.orm import Session
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError, 
    ChatAdminRequiredError,
    UserBannedInChannelError
)

from src.models.monitored_source import OutputChannel, OutputType
from src.models.notification_channel import NotificationChannel
from src.utils.db import db_session
from src.utils.text import TextFormatter
from src.utils.exceptions import OutputServiceError


class OutputService:
    """Service for managing output channels and message delivery."""
    
    def __init__(self, db: Session, telegram_client: Optional[TelegramClient] = None) -> None:
        """Initialize output service."""
        self.db = db
        self.telegram_client = telegram_client
        self.text_formatter = TextFormatter()
        self._queue = asyncio.Queue()
        self._running = False
        self._worker_task = None
        
    def _update_channel_stats(self, db: Session, channel: OutputChannel, success: bool) -> None:
        """Update channel statistics after message send attempt."""
        try:
            stmt = update(OutputChannel).where(OutputChannel.id == channel.id)
            
            if success:
                # Use SQLAlchemy update for atomic updates
                stmt = stmt.values({
                    OutputChannel.message_count: case(
                        (OutputChannel.message_count.is_(None), 1),
                        else_=OutputChannel.message_count + 1
                    ),
                    OutputChannel.last_sent: datetime.utcnow(),
                    OutputChannel.error_count: 0
                })
            else:
                stmt = stmt.values({
                    OutputChannel.error_count: case(
                        (OutputChannel.error_count.is_(None), 1),
                        else_=OutputChannel.error_count + 1
                    )
                })
                
            db.execute(stmt)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating channel stats: {e}")
            db.rollback()
            
    async def start(self):
        """Start the output service."""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting output service")
        
        # Start message processing worker
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the output service."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            
        logger.info("Stopped output service")

    async def _process_queue(self):
        """Process messages in the queue."""
        try:
            while self._running:
                try:
                    # Get next message from queue
                    message = await self._queue.get()
                    
                    # Process message
                    await self.send_message(message)
                    
                    self._queue.task_done()
                    
                except asyncio.CancelledError:
                    break
                    
                except Exception as e:
                    logger.error(f"Error processing output message: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Stopping output message processing")

    async def send_message(
        self, 
        channel: OutputChannel,
        content: Union[str, Dict[str, Any]],
        attachments: Optional[List[str]] = None,
        sentiment: Optional[float] = None,
        summary: Optional[str] = None
    ) -> bool:
        """Send message to output channel."""
        try:
            # Format message with metadata
            formatted_msg = self.text_formatter.format_message(
                message=content if isinstance(content, str) else str(content)
            )
            
            success = False
            
            if str(channel.type) == str(OutputType.TELEGRAM):
                success = await self._send_telegram(
                    channel_id=str(channel.identifier),
                    message=formatted_msg,
                    attachments=attachments or []
                )
            
            elif str(channel.type) == str(OutputType.DISCORD):
                success = await self._send_discord(
                    webhook_url=channel.webhook_url,
                    message=formatted_msg,
                    attachments=attachments or []
                )
            
            # Update channel stats in separate context
            with db_session() as db:
                db_channel = db.query(OutputChannel).get(channel.id)
                if db_channel:
                    self._update_channel_stats(db, db_channel, success)
            
            return success
            
        except Exception as e:
            logger.exception(f"Error sending message to {channel.type} channel {getattr(channel, 'identifier', 'unknown')}: {e}")
            raise OutputServiceError(f"Message sending failed: {str(e)}")
    
    async def _send_telegram(
        self,
        channel_id: Union[int, str],
        message: str,
        attachments: List[str] = []
    ) -> bool:
        """Send message to Telegram channel."""
        if not self.telegram_client:
            logger.error("No Telegram client configured")
            return False
            
        try:
            # Handle attachments
            if attachments:
                media = []
                async with aiohttp.ClientSession() as session:
                    for url in attachments[:10]:  # Limit to 10 attachments
                        try:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    media.append(await response.read())
                        except Exception as e:
                            logger.warning(f"Failed to fetch attachment {url}: {e}")
                
                if media:
                    await self.telegram_client.send_file(
                        channel_id,
                        media,
                        caption=message[:1024]  # Telegram caption limit
                    )
                else:
                    await self.telegram_client.send_message(channel_id, message)
            else:
                await self.telegram_client.send_message(channel_id, message)
                
            return True
            
        except (ChannelPrivateError, ChatAdminRequiredError, UserBannedInChannelError) as e:
            logger.error(f"Telegram channel access error for {channel_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Error sending Telegram message to {channel_id}: {e}")
            return False
            
    async def _send_discord(
        self,
        webhook_url: str,
        message: str,
        attachments: List[str] = []
    ) -> bool:
        """Send message to Discord channel via webhook."""
        try:
            payload = {
                "content": message[:2000],  # Discord message limit
                "embeds": []
            }
            
            # Add attachments as embeds
            if attachments:
                for url in attachments[:10]:  # Discord limit
                    payload["embeds"].append({
                        "image": {"url": url}
                    })
                    
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 204  # Discord returns 204 on success
                    
        except Exception as e:
            logger.exception(f"Error sending Discord webhook: {e}")
            return False

    async def queue_message(self, message: str, channels: Optional[List[NotificationChannel]] = None):
        """Queue a message for sending."""
        await self._queue.put({
            'message': message,
            'channels': channels
        })
