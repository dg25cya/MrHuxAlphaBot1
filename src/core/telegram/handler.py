"""Telegram message handling and processing."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from telethon import events, TelegramClient
from loguru import logger

from .queue import MessageQueue, MessageRateLimiter
from ..services.token_patterns import EnhancedTokenParser, TokenContext
from ..services.parser import TokenParser
from ..services.scorer import TokenScorer
from ...api.clients.dexscreener import DexscreenerClient
from ...api.clients.rugcheck import RugcheckClient
from ...utils.formatters import format_alert_message
from ...models.token import Token
from ...core.monitoring import (
    MESSAGE_PROCESSING_COUNT,
    TOKEN_VALIDATION_COUNT,
    TOKEN_PROCESSING_TIME,
    ALERT_GENERATION_COUNT
)

class MessageHandler:
    """Handler for processing Telegram messages."""
    
    def __init__(
        self,
        client: TelegramClient,
        dexscreener: DexscreenerClient,
        rugcheck: RugcheckClient,
        alert_channel_id: int,
        rate_limit: int = 60,
        window: int = 60
    ):
        self.client = client
        self.dexscreener = dexscreener
        self.rugcheck = rugcheck
        self.alert_channel_id = alert_channel_id
        
        # Initialize components
        self.queue = MessageQueue(
            rate_limiter=MessageRateLimiter(rate_limit, window)
        )
        self.token_parser = EnhancedTokenParser()
        self.basic_parser = TokenParser()
        self.scorer = TokenScorer()
        
        # Start message processing
        self.setup_handlers()
        
    def setup_handlers(self) -> None:
        """Set up message event handlers."""
        
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            """Handle incoming messages."""
            try:
                # Record message receipt
                MESSAGE_PROCESSING_COUNT.record_message(
                    success=True,
                    group_id=event.chat_id,
                    timestamp=datetime.utcnow()
                )
                
                # Queue message for processing
                await self.queue.put(
                    group_id=event.chat_id,
                    message={
                        "text": event.message.text,
                        "chat_id": event.chat_id,
                        "message_id": event.message.id,
                        "date": event.message.date
                    }
                )
                
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
                MESSAGE_PROCESSING_COUNT.record_message(
                    success=False,
                    group_id=event.chat_id,
                    timestamp=datetime.utcnow()
                )
        
        # Start message processing
        self.client.loop.create_task(
            self.queue.process_messages(
                handler=self.process_message,
                error_handler=self.handle_error
            )
        )
        
    async def process_message(self, message: Dict[str, Any]):
        """
        Process a queued message.
        
        Args:
            message: Message data including text and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract tokens with context
            contexts = self.token_parser.extract_with_context(message["text"])
            contexts = self.token_parser.filter_duplicates(contexts)
            
            for ctx in contexts:
                # Use TokenParser to parse message and get token data
                token_parser = TokenParser()
                token_data_list = await token_parser.parse_message(message["text"], message["chat_id"], message["message_id"])
                
                for token_data in token_data_list:
                    # Add contextual information
                    token_data.update({
                        "mention_context": ctx.surrounding_text if hasattr(ctx, 'surrounding_text') else None,
                        "mention_sentiment": self.token_parser.analyze_sentiment(ctx) if hasattr(self.token_parser, 'analyze_sentiment') else None,
                        "mention_source": getattr(ctx, 'source', None),
                        "mention_confidence": getattr(ctx, 'confidence', None)
                    })
                    
                    # Score token
                    score = await self.scorer.score_token(token_data)
                    if not score:
                        continue
                        
                    # Record successful validation
                    TOKEN_VALIDATION_COUNT.record_validation(
                        success=True,
                        source=getattr(ctx, 'source', 'unknown'),
                        timestamp=datetime.utcnow()
                    )
                    
                    # Generate alert if scores are high enough
                    if score.safety_score >= 60 or score.hype_score >= 60:
                        alert_text = format_alert_message({
                            **token_data,
                            "safety_score": score.safety_score,
                            "hype_score": score.hype_score,
                            "risk_factors": score.risk_factors
                        })
                        
                        # Send alert
                        try:
                            await self.client.send_message(
                                self.alert_channel_id,
                                alert_text
                            )
                            ALERT_GENERATION_COUNT.record_alert(
                                success=True,
                                alert_type="token_alert",
                                timestamp=datetime.utcnow()
                            )
                        except Exception as e:
                            logger.error(f"Error sending alert: {str(e)}")
                            ALERT_GENERATION_COUNT.record_alert(
                                success=False,
                                alert_type="token_alert",
                                timestamp=datetime.utcnow()
                            )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            TOKEN_VALIDATION_COUNT.record_validation(
                success=False,
                source="unknown",
                timestamp=datetime.utcnow()
            )
            
        finally:
            # Record processing time
            duration = (datetime.utcnow() - start_time).total_seconds()
            TOKEN_PROCESSING_TIME.record_processing_time(
                duration,
                timestamp=datetime.utcnow()
            )
            
    async def handle_error(self, error: Exception):
        """Handle processing errors."""
        logger.error(f"Message processing error: {str(error)}")
        # Could add error reporting, monitoring alerts, etc. here
