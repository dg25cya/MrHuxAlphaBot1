"""Telegram message poster for sending alerts."""
import asyncio
from typing import Dict, Any, Optional, List

from loguru import logger
from prometheus_client import Counter, Histogram

from src.config.settings import get_settings
from src.core.telegram.client import get_client
from src.utils import get_utc_now
from src.models.token import Token

settings = get_settings()

# Metrics
ALERT_SEND_TIME = Histogram(
    'alert_send_time_seconds',
    'Time spent sending alerts'
)

ALERTS_SENT = Counter(
    'alerts_sent_total',
    'Number of alerts sent',
    ['status', 'alert_type']
)

class AlertPoster:
    """Service for posting alerts to Telegram channels."""
    
    def __init__(self) -> None:
        """Initialize the alert poster."""
        self.output_channel_id = settings.output_channel_id
        self.rate_limit = 2.0  # Seconds between messages
        self.last_sent = 0.0
        self.client = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the Telegram client."""
        if self.client is None or not self.client.is_connected():
            self.client = await get_client()
            
    async def send_token_alert(self, token: Token, metrics: Dict[str, Any], alert_type: str = "new_token") -> bool:
        """
        Send a token alert to the output channel.
        
        Args:
            token: The token object
            metrics: The token metrics dictionary
            alert_type: The type of alert
            
        Returns:
            bool: True if sent successfully
        """
        try:
            with ALERT_SEND_TIME.time():
                await self.initialize()
                
                # Rate limiting
                async with self._lock:
                    now = get_utc_now().timestamp()
                    if now - self.last_sent < self.rate_limit:
                        await asyncio.sleep(self.rate_limit - (now - self.last_sent))
                    self.last_sent = get_utc_now().timestamp()
                
                if not self.output_channel_id:
                    logger.warning("Output channel ID not configured")
                    return False
                
                # Ensure client is initialized
                if not self.client:
                    logger.error("Telegram client not initialized")
                    return False
                
                # Format message
                message = self._format_token_message(token, metrics)
                
                # Send message
                result = await self.client.send_message(
                    self.output_channel_id,
                    message["text"],
                    parse_mode='html',
                    link_preview=False
                )
                
                if result:
                    ALERTS_SENT.labels(status="success", alert_type=alert_type).inc()
                    return True
                    
                ALERTS_SENT.labels(status="failed", alert_type=alert_type).inc()
                return False
                
        except Exception as e:
            logger.exception(f"Failed to send alert: {e}")
            ALERTS_SENT.labels(status="error", alert_type=alert_type).inc()
            return False
            
    def _format_token_message(
        self, 
        token: Token,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format token alert message for Telegram.
        
        Args:
            token: The token object
            metrics: The token metrics dictionary
            
        Returns:
            Dict with text and buttons
        """
        # Basic message template
        symbol = token.symbol or "UNKNOWN"
        address = token.address
        
        # Prepare metrics data
        price = f"${float(metrics.get('price', 0)):.8f}" if metrics.get('price') else "Unknown"
        market_cap = f"${float(metrics.get('market_cap', 0)):,.0f}" if metrics.get('market_cap') else "Unknown"
        liquidity = f"${float(metrics.get('liquidity', 0)):,.0f}" if metrics.get('liquidity') else "Unknown"
        volume_24h = f"${float(metrics.get('volume_24h', 0)):,.0f}" if metrics.get('volume_24h') else "Unknown"
        holder_count = f"{metrics.get('holder_count', 0):,}" if metrics.get('holder_count') is not None else "Unknown"
        
        # Build safety indicators
        safety_indicators = []
        if metrics.get('is_mint_disabled'):
            safety_indicators.append("✅ Mint revoked")
        else:
            safety_indicators.append("⚠️ Mint active")
            
        if metrics.get('is_lp_locked'):
            safety_indicators.append("✅ LP locked")
        else:
            safety_indicators.append("⚠️ LP not locked")
            
        safety_text = " | ".join(safety_indicators)
        
        # Generate verdict based on scores
        verdict = self._get_verdict(
            metrics.get('safety_score'),
            metrics.get('hype_score')
        )
        
        # Format message text
        text = f"""
🚨 NEW TOKEN DETECTED: ${symbol}
📜 Contract: <code>{address}</code>
📊 Volume: {volume_24h} | LP: {liquidity}
👥 Holders: {holder_count}

🛡️ Safety: {safety_text}
📈 Chart: <a href="https://dexscreener.com/solana/{address}">Dexscreener</a>

Verdict: {verdict}
        """.strip()
        
        return {
            "text": text,
            "buttons": None  # Can add inline buttons here if needed
        }
        
    def _get_verdict(self, safety_score: Optional[float], hype_score: Optional[float]) -> str:
        """Get verdict emoji based on scores."""
        if safety_score is None or hype_score is None:
            return "⚠️ UNKNOWN"
            
        if safety_score < 30:
            return "❌ RISKY"
            
        if safety_score >= 70 and hype_score >= 70:
            return "🔥 HOT PLAY"
            
        if safety_score >= 70:
            return "✅ SAFE"
            
        if hype_score >= 70:
            return "🚀 HIGH HYPE"
            
        return "⚠️ NEUTRAL"

async def send_notification(message: str) -> bool:
    """Send notification message to admin channel."""
    try:
        client = await get_client()
        # Use the output channel as fallback for notifications
        notification_channel = getattr(settings, "notification_channel_id", None)
        if not notification_channel:
            notification_channel = settings.output_channel_id
        
        if not notification_channel:
            logger.warning("No notification channel configured, skipping notification")
            return False
            
        await client.send_message(
            notification_channel,
            message,
            parse_mode='html'
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False