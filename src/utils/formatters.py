"""Alert message formatting utilities."""
from typing import Dict, Any, List, Optional
from src.models.monitored_source import OutputType

def format_currency(amount: float) -> str:
    """Format currency amount with K/M/B suffixes."""
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    else:
        return f"${amount:.0f}"

def format_holders(count: int) -> str:
    """Format holder count with K suffix if needed."""
    if count >= 1_000:
        return f"{count/1_000:.1f}K"
    return str(count)

def get_safety_emoji(score: float) -> str:
    """Get safety indicator emoji based on score."""
    if score >= 80:
        return "🛡️"
    elif score >= 60:
        return "✅"
    elif score >= 40:
        return "⚠️"
    else:
        return "⛔"

def get_hype_emoji(score: float) -> str:
    """Get hype indicator emoji based on score."""
    if score >= 80:
        return "🔥"
    elif score >= 60:
        return "📈"
    elif score >= 40:
        return "📊"
    else:
        return "💤"

def format_alert_message(token_data: Dict[str, Any]) -> str:
    """
    Format token alert message.
    
    Example:
    🚨 NEW TOKEN DETECTED: $TOKEN
    📜 Contract: [address]
    📊 Volume: $123K | LP: $45K
    👥 Holders: 398
    🔥 3 whale buys detected

    🛡️ Safety: Mint revoked, LP locked
    📈 Chart: [Dexscreener link]

    Verdict: 🔥 HOT PLAY
    """
    # Extract data
    symbol = token_data.get("symbol", "UNKNOWN")
    address = token_data.get("address", "")
    volume = token_data.get("volume_24h", 0)
    liquidity = token_data.get("liquidity", 0)
    holders = token_data.get("holder_count", 0)
    whale_buys = token_data.get("whale_buys_24h", 0)
    safety_score = token_data.get("safety_score", 0)
    hype_score = token_data.get("hype_score", 0)
    
    # Get safety factors
    safety_factors = []
    if token_data.get("is_mint_disabled"):
        safety_factors.append("Mint revoked")
    if token_data.get("is_lp_locked"):
        safety_factors.append("LP locked")
    
    # Format message
    lines = [
        f"🚨 NEW TOKEN DETECTED: ${symbol}",
        f"📜 Contract: {address}",
        f"📊 Volume: {format_currency(volume)} | LP: {format_currency(liquidity)}",
        f"👥 Holders: {format_holders(holders)}"
    ]
    
    # Add whale buys if any
    if whale_buys > 0:
        lines.append(f"🔥 {whale_buys} whale buys detected")
        
    lines.extend([
        "",  # Empty line
        f"{get_safety_emoji(safety_score)} Safety: {', '.join(safety_factors)}",
        f"📈 Chart: https://dexscreener.com/solana/{address}",
        "",  # Empty line
    ])
    
    # Add verdict
    if safety_score >= 60 and hype_score >= 60:
        verdict = "🔥 HOT PLAY"
    elif safety_score >= 60:
        verdict = "✅ SAFE PLAY"
    elif hype_score >= 60:
        verdict = "⚠️ DEGEN PLAY"
    else:
        verdict = "⛔ STAY AWAY"
        
    lines.append(f"Verdict: {verdict}")
    
    return "\n".join(lines)

def format_token_update(
    token_data: Dict[str, Any],
    price_change: float,
    time_period: str = "1h"
) -> str:
    """Format token price/volume update message."""
    symbol = token_data.get("symbol", "UNKNOWN")
    price = token_data.get("price", 0)
    volume = token_data.get("volume_24h", 0)
    
    emoji = "🟢" if price_change > 0 else "🔴"
    change = f"+{price_change:.1f}%" if price_change > 0 else f"{price_change:.1f}%"
    
    return (
        f"${symbol} Update ({time_period})\n"
        f"💵 Price: ${price:.4f}\n"
        f"{emoji} Change: {change}\n"
        f"📊 Volume: {format_currency(volume)}"
    )

def format_message(
    message: str,
    output_type: OutputType,
    custom_format: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> str:
    """Format message for different output channels."""
    if custom_format:
        try:
            return custom_format.format(message=message, **(data or {}))
        except Exception as e:
            pass

    if output_type == OutputType.TELEGRAM:
        return _format_telegram(message, data)
    elif output_type == OutputType.DISCORD:
        return _format_discord(message, data)
    elif output_type == OutputType.X:
        return _format_x(message, data)
    
    return message

def _format_telegram(message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Format message for Telegram."""
    # Support basic HTML formatting
    message = message.replace('&', '&amp;')
    message = message.replace('<', '&lt;')
    message = message.replace('>', '&gt;')
    
    # Convert Markdown-style formatting to HTML
    message = message.replace('**', '<b>')
    message = message.replace('__', '</b>')
    message = message.replace('_', '<i>')
    message = message.replace('_', '</i>')
    message = message.replace('`', '<code>')
    message = message.replace('`', '</code>')
    
    if data and 'url' in data:
        message += f"\n\n🔗 <a href='{data['url']}'>View Details</a>"
    
    return message

def _format_discord(message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Format message for Discord."""
    # Convert HTML to Discord markdown
    message = message.replace('<b>', '**')
    message = message.replace('</b>', '**')
    message = message.replace('<i>', '_')
    message = message.replace('</i>', '_')
    message = message.replace('<code>', '`')
    message = message.replace('</code>', '`')
    
    if data:
        if 'url' in data:
            message += f"\n\n🔗 {data['url']}"
        if 'fields' in data:
            for field in data['fields']:
                message += f"\n**{field['name']}:** {field['value']}"
    
    return message

def _format_x(message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Format message for X (Twitter)."""
    # Remove HTML/markdown formatting
    message = message.replace('<b>', '')
    message = message.replace('</b>', '')
    message = message.replace('<i>', '')
    message = message.replace('</i>', '')
    message = message.replace('<code>', '')
    message = message.replace('</code>', '')
    
    # Ensure message fits in tweet
    if len(message) > 280:
        message = message[:277] + "..."
        
    if data and 'url' in data:
        if len(message) + len(data['url']) + 2 <= 280:
            message += f"\n\n{data['url']}"
    
    return message
