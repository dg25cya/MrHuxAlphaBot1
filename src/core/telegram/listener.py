"""Telegram message listener and handler."""
from typing import Optional, List, Dict, Any, Callable
from functools import wraps
import asyncio
import re

from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from telethon import events, TelegramClient
from telethon.events import NewMessage
from telethon.tl.custom import Message

from src.core.services.parser import TokenParser
from src.core.telegram.metrics import (
    log_message_processed,
    log_db_error,
    time_message_processing
)
from src.models.group import MonitoredGroup
from src.models.mention import TokenMention
from src.models.token import Token
from src.utils.db import db_session
from src.utils import get_utc_now
from src.database import SessionLocal
from src.config.settings import get_settings
from src.core.services.text_analysis import deepseek_analyze
from src.models.output_channel import OutputChannel, OutputType
from src.core.services.output_service import OutputService
from src.core.services.token_monitor import TokenMonitor

settings = get_settings()

# Batch processing settings
BATCH_SIZE = 10
BATCH_TIMEOUT = 5  # seconds

# Singleton for real-time token monitoring
TOKEN_MONITOR = TokenMonitor()

class MessageBatch:
    """Batch message processor for improved performance."""
    def __init__(self) -> None:
        self.messages = []
        self.lock = asyncio.Lock()
        self.processing = False
        
    async def add_message(self, event: NewMessage.Event, session: Optional[Session] = None):
        """Add message to batch for processing."""
        async with self.lock:
            self.messages.append((event, session))
            if len(self.messages) >= BATCH_SIZE and not self.processing:
                await self.process_batch()
                
    async def process_batch(self):
        """Process a batch of messages."""
        async with self.lock:
            if not self.messages or self.processing:
                return
                
            self.processing = True
            batch = self.messages[:BATCH_SIZE]
            self.messages = self.messages[BATCH_SIZE:]
            
        try:
            # Process messages in parallel
            await asyncio.gather(*[
                handle_new_message(event, session)
                for event, session in batch
            ])
        except Exception as e:
            logger.exception(f"Error processing message batch: {e}")
        finally:
            self.processing = False
            
    async def start_background_processor(self):
        """Start background batch processor."""
        while True:
            await asyncio.sleep(BATCH_TIMEOUT)
            if self.messages:
                await self.process_batch()

# Global batch processor
message_batch = MessageBatch()

def with_db_retry(max_retries: int = 3, delay: float = 0.1) -> Callable:
    """Decorator to retry database operations."""
    def decorator(func) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except SQLAlchemyError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                        continue
                    log_db_error(func.__name__)
                    logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                    raise
            return None
        return wrapper
    return decorator

@with_db_retry(max_retries=3)
async def process_token(
    token_address: str,
    message_text: str,
    group_id: int,
    message_id: int,
    db: Session
) -> Optional[Token]:
    """
    Process a found token, create or update records, and send alerts.
    
    Args:
        token_address: The Solana token address
        message_text: The full message text
        group_id: Telegram group ID
        message_id: Telegram message ID
        db: Database session
    
    Returns:
        Token: Created or updated token record
    """
    try:
        # Get monitored group first
        group = db.query(MonitoredGroup).filter(
            MonitoredGroup.group_id == group_id
        ).first()
        
        if not group:
            logger.warning(f"Message from unknown group {group_id}")
            log_message_processed("unmonitored_group")
            return None
            
        # Check if token exists
        token = db.query(Token).filter(Token.address == token_address).first()
        current_time = get_utc_now()
        
        if not token:
            # Create new token record
            token = Token(
                address=token_address,
                first_seen_at=current_time,
                last_updated_at=current_time
            )
            db.add(token)
            db.flush()  # This ensures token.id is set
        else:
            # Update token's last_updated_at
            setattr(token, 'last_updated_at', current_time)
        
        # Create mention record
        mention = TokenMention(
            token_id=token.id,
            group_id=group.id,
            message_id=message_id,
            message_text=message_text,
            mentioned_at=current_time
        )
        db.add(mention)
        db.commit()  # Commit all changes
        
        # Analyze with DeepSeek AI
        try:
            ai_analysis = await deepseek_analyze(message_text)
            sentiment = ai_analysis.get('sentiment', 'neutral')
            summary = ai_analysis.get('summary', 'No summary available')
        except Exception as e:
            logger.warning(f"DeepSeek analysis failed: {e}")
            sentiment = 'neutral'
            summary = 'AI analysis unavailable'
        
        # After storing the mention, trigger real-time analysis
        try:
            await TOKEN_MONITOR.add_token(token_address, db=db)
        except Exception as e:
            logger.error(f"TokenMonitor analysis failed: {e}")
        
        # Send alert to output channels
        await send_token_alert(token, message_text, group, sentiment, summary, db)
        
        log_message_processed("success")
        return token
    except Exception as e:
        logger.error(f"Error processing token: {e}")
        return None

async def send_token_alert(token: Token, message_text: str, group: MonitoredGroup, sentiment: str, summary: str, db: Session):
    """Send token alert to all output channels."""
    try:
        # Get all active output channels
        output_channels = db.query(OutputChannel).filter(OutputChannel.is_active == True).all()
        
        if not output_channels:
            logger.warning("No active output channels found")
            return
        
        # Format alert message
        alert_message = f"""
🚨 **NEW TOKEN DETECTED** 🚨

🪙 **Token:** `{token.address}`
📱 **Source:** {group.name or group.group_id}
💬 **Message:** {message_text[:200]}{'...' if len(message_text) > 200 else ''}

🤖 **AI Analysis:**
• **Sentiment:** {sentiment}
• **Summary:** {summary}

⏰ **Detected:** {get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🔗 **View on Solscan:** https://solscan.io/token/{token.address}
"""
        
        # Send to each output channel
        for channel in output_channels:
            try:
                if channel.type == OutputType.TELEGRAM:
                    # Send to Telegram channel
                    from src.core.telegram.client import client
                    if client and client.is_connected():
                        await client.send_message(
                            entity=channel.identifier,
                            message=alert_message,
                            parse_mode='markdown'
                        )
                        logger.info(f"Alert sent to Telegram channel {channel.identifier}")
                elif channel.type == OutputType.DISCORD:
                    # Send to Discord webhook
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            channel.identifier,
                            json={"content": alert_message}
                        )
                        logger.info(f"Alert sent to Discord webhook {channel.identifier}")
            except Exception as e:
                logger.error(f"Failed to send alert to channel {channel.identifier}: {e}")
                
    except Exception as e:
        logger.error(f"Error sending token alert: {e}")

async def handle_new_message(event: NewMessage.Event, session: Optional[Session] = None):
    """Handle new messages in monitored groups."""
    if not hasattr(event, 'message') or not isinstance(event.message, Message):
        log_message_processed("invalid_message")
        return
    msg = event.message
    if not msg.text:
        log_message_processed("no_text")
        return
    # Ignore bot commands
    if msg.text.startswith('/'):
        log_message_processed("bot_command")
        return
    try:
        with time_message_processing():
            # Extract necessary fields and verify they are not None
            if not msg.text or not msg.chat_id or not msg.id:
                log_message_processed("missing_fields")
                return
            # --- FILTER LOGIC ---
            from src.models.monitored_source import MonitoredSource
            from src.utils.db import db_session
            with db_session() as db:
                source = db.query(MonitoredSource).filter(MonitoredSource.identifier == str(msg.chat_id), MonitoredSource.is_active == True).first()
                if source and source.custom_filters:
                    filters = source.custom_filters.get("keywords", [])
                    if filters:
                        matched = False
                        for f in filters:
                            if f:
                                if any(c in f for c in "^$.*+?[]{}|()"):
                                    try:
                                        if re.search(f, msg.text, re.IGNORECASE):
                                            matched = True
                                            break
                                    except re.error:
                                        continue
                                elif f.lower() in msg.text.lower():
                                    matched = True
                                    break
                        if not matched:
                            log_message_processed("filtered_out")
                            return
            # --- END FILTER LOGIC ---
            # Use an instance of TokenParser
            parser = TokenParser()
            # Extract tokens from message text and images (async)
            tokens = await parser.parse_message(
                msg.text, 
                msg.chat_id, 
                msg.id
            )
            if not tokens:
                log_message_processed("no_tokens")
                return
            # Use provided session or get a new one from generator
            db = session
            if db is None:
                try:
                    db = SessionLocal()
                except Exception as e:
                    logger.error(f"Failed to create database session: {e}")
                    log_db_error("create_session")
                    log_message_processed("db_session_error")
                    return
            try:
                for token_match in tokens:
                    result = await process_token(
                        token_address=token_match["address"],
                        message_text=msg.text,
                        group_id=msg.chat_id,
                        message_id=msg.id,
                        db=db
                    )
                    if result:
                        logger.info(
                            f"Processed token {token_match['address']} "
                            f"from group {msg.chat_id}"
                        )
            finally:
                if session is None and db:
                    try:
                        db.close()
                    except Exception as e:
                        logger.error(f"Error closing database session: {e}")
                        log_db_error("close_session")
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        log_message_processed("processing_error")

async def setup_message_handler(client: TelegramClient, db=None, text_analyzer=None):
    """Setup message handler for the bot."""
    # Start the batch processor
    asyncio.create_task(message_batch.start_background_processor())
    
    async def batch_message_handler(event: NewMessage.Event):
        """Handler that adds messages to batch processor."""
        await message_batch.add_message(event)
    
    # Register handler for new messages
    client.add_event_handler(
        batch_message_handler,
        events.NewMessage(func=lambda e: True)  # Handle all new messages
    )
    
    logger.info("Message handler and batch processor setup complete")
