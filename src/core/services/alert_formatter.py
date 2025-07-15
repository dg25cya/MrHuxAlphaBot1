"""Enhanced alert formatting service for token notifications."""
from typing import Dict, Any, Optional

from src.config.settings import get_settings
# Removing formatters import as it seems to be missing or has a different structure

settings = get_settings()

# Helper functions for formatting (replacing the missing imports)
def format_number(num, precision=2) -> None:
    """Format a number with appropriate precision."""
    if num is None:
        return "N/A"
    return f"{num:,.{precision}f}"

def format_percentage(num, include_plus=True) -> None:
    """Format a percentage with +/- sign."""
    if num is None:
        return "N/A"
    sign = "+" if num > 0 and include_plus else ""
    return f"{sign}{num:.2f}%"

def format_usd(num, include_symbol=True) -> None:
    """Format a USD amount."""
    if num is None:
        return "N/A"
    
    if num >= 1_000_000_000:
        formatted = f"${num/1_000_000_000:.2f}B" if include_symbol else f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        formatted = f"${num/1_000_000:.2f}M" if include_symbol else f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        formatted = f"${num/1_000:.2f}K" if include_symbol else f"{num/1_000:.2f}K"
    else:
        formatted = f"${num:.2f}" if include_symbol else f"{num:.2f}"
    
    return formatted

class AlertFormatter:
    """Service for formatting token alerts with rich analytics."""

    def __init__(self) -> None:
        """Initialize the alert formatter."""
        self.settings = get_settings()
        
        # Alert templates
        self.templates = {
            "new_token": "🚨 New Token Alert\n\n{body}",
            "price_alert": "💰 Price Alert\n\n{body}",
            "momentum_alert": "📈 Momentum Alert\n\n{body}",
            "whale_alert": "🐋 Whale Alert\n\n{body}"
        }
        
        # Emoji indicators
        self.trend_emojis = {
            "very_bullish": "🚀",
            "bullish": "📈",
            "neutral": "➡️",
            "bearish": "📉",
            "very_bearish": "💥"
        }
        
        self.safety_emojis = {
            "safe": "✅",
            "caution": "⚠️",
            "dangerous": "⛔"
        }
        
        self.hype_emojis = {
            "extreme": "🔥",
            "high": "⚡",
            "medium": "📊",
            "low": "💤"
        }

    def _get_trend_emoji(self, price_change: float) -> str:
        """Get appropriate trend emoji based on price change."""
        if price_change >= 50:
            return self.trend_emojis["very_bullish"]
        elif price_change >= 10:
            return self.trend_emojis["bullish"]
        elif price_change <= -50:
            return self.trend_emojis["very_bearish"]
        elif price_change <= -10:
            return self.trend_emojis["bearish"]
        return self.trend_emojis["neutral"]

    def _get_safety_emoji(self, safety_score: float) -> str:
        """Get appropriate safety emoji based on score."""
        if safety_score >= 80:
            return self.safety_emojis["safe"]
        elif safety_score >= 50:
            return self.safety_emojis["caution"]
        return self.safety_emojis["dangerous"]

    def format_token_alert(
        self,
        token_data: Dict[str, Any],
        alert_type: str = "new_token"
    ) -> str:
        """
        Format a token alert with rich analytics.
        
        Args:
            token_data: Token data including metrics and analysis
            alert_type: Type of alert to format
        
        Returns:
            Formatted alert message
        """
        # Extract key metrics
        address = token_data["address"]
        price = token_data.get("price", 0)
        mcap = token_data.get("market_cap", 0)
        holders = token_data.get("holders", 0)
        liquidity = token_data.get("liquidity", 0)
        
        # Get validation and analysis data
        validation = token_data.get("validation", {})
        momentum = token_data.get("momentum", {})
        score = token_data.get("score", {})
        
        # Format header with basic info
        header = [
            f"Token: `{address}`",
            f"Price: ${format_number(price)}",
            f"MCap: ${format_usd(mcap)}",
            f"Liquidity: ${format_usd(liquidity)}"
        ]
        
        # Add momentum and analysis
        if momentum:
            hype_level = momentum.get("hype_level", "low")
            mention_count = momentum.get("mention_count", 0)
            momentum_score = momentum.get("momentum_score", 0)
            
            analysis = [
                f"\n📊 Analysis:",
                f"{self.hype_emojis[hype_level]} Hype Level: {hype_level.title()}",
                f"👥 Recent Mentions: {mention_count}",
                f"📈 Momentum Score: {format_number(momentum_score)}"
            ]
        else:
            analysis = []
        
        # Add safety metrics
        if validation:
            safety_score = validation.get("metrics", {}).get("safety_score", 0)
            safety = [
                f"\n🛡️ Safety:",
                f"{self._get_safety_emoji(safety_score)} Score: {format_number(safety_score)}",
                f"👥 Holders: {format_number(holders)}"
            ]
            
            # Add any failed checks as warnings
            failed_checks = [
                check for check, result in validation.get("checks", {}).items()
                if not result.get("passed") and result.get("required")
            ]
            if failed_checks:
                safety.append(f"⚠️ Warnings: {', '.join(failed_checks)}")
        else:
            safety = []
        
        # Add links
        links = [
            f"\n🔍 Links:",
            f"• Birdeye: https://birdeye.so/token/{address}",
            f"• Dexscreener: https://dexscreener.com/solana/{address}",
            f"• Solscan: https://solscan.io/token/{address}"
        ]
        
        # Combine sections
        sections = header + analysis + safety + links
        
        # Use template
        template = self.templates.get(alert_type, self.templates["new_token"])
        body = "\n".join(sections)
        
        return template.format(body=body)

    def format_price_alert(
        self,
        token_data: Dict[str, Any],
        price_change: float
    ) -> str:
        """Format a price movement alert."""
        trend_emoji = self._get_trend_emoji(price_change)
        body = self.format_token_alert(token_data, "price_alert")
        
        # Add price change header
        price_header = (
            f"{trend_emoji} Price Change: {format_percentage(price_change)}%\n"
        )
        return price_header + body

    def format_momentum_alert(
        self,
        token_data: Dict[str, Any],
        momentum_change: float
    ) -> str:
        """Format a momentum shift alert."""
        momentum = token_data.get("momentum", {})
        hype_level = momentum.get("hype_level", "low").title()
        hype_emoji = self.hype_emojis[hype_level.lower()]
        
        body = self.format_token_alert(token_data, "momentum_alert")
        
        # Add momentum header
        momentum_header = (
            f"{hype_emoji} Momentum Shift: {format_percentage(momentum_change)}%\n"
            f"New Hype Level: {hype_level}\n"
        )
        return momentum_header + body

    def format_whale_alert(
        self,
        token_data: Dict[str, Any],
        amount: float,
        transaction_type: str
    ) -> str:
        """Format a whale transaction alert."""
        emoji = "🔴" if transaction_type.lower() == "sell" else "🟢"
        body = self.format_token_alert(token_data, "whale_alert")
        
        # Add whale transaction header
        whale_header = (
            f"{emoji} Whale {transaction_type.title()}: ${format_usd(amount)}\n"
        )
        return whale_header + body
