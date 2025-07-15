"""Token parsing patterns and validation."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TokenPattern:
    """Token pattern definition."""
    name: str
    pattern: str
    group_index: int = 1  # Index of the group containing the address
    confidence: float = 1.0  # How confident we are that matches are really tokens

    def find_matches(self, text: str) -> List[Dict[str, Any]]:
        """Find all matches of this pattern in the given text.
        
        Args:
            text: The text to search for matches
            
        Returns:
            List of dictionaries with matched address and confidence
        """
        matches = []
        for match in re.finditer(self.pattern, text):
            try:
                address = match.group(self.group_index)
                matches.append({
                    "address": address,
                    "confidence": self.confidence,
                    "pattern": self.name
                })
            except (IndexError, AttributeError) as e:
                continue
        return matches

# Standard patterns for token detection
TOKEN_PATTERNS = [
    TokenPattern(
        name="solana_address",
        pattern=r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b',
        confidence=0.7  # Lower confidence as it might catch non-token addresses
    ),
    TokenPattern(
        name="dexscreener",
        pattern=r'dexscreener\.com/solana/([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=1.0
    ),
    TokenPattern(
        name="birdeye",
        pattern=r'birdeye\.so/token/([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=1.0
    ),
    TokenPattern(
        name="solscan",
        pattern=r'solscan\.io/token/([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=1.0
    ),
    TokenPattern(
        name="pump_fun",
        pattern=r'pump\.fun/token/([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=1.0
    ),
    TokenPattern(
        name="bonk_fun",
        pattern=r'bonk\.fun/token/([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=1.0
    ),
    TokenPattern(
        name="token_in_text",
        pattern=r'(?i)(?:token|contract|address)[^\n]*?([1-9A-HJ-NP-Za-km-z]{32,44})',
        confidence=0.9
    )
]

# Additional patterns for context extraction
PRICE_PATTERN = r'\$\s*([\d,.]+)'
PERCENTAGE_PATTERN = r'(?:[-+]?\d+(?:\.\d+)?%)|(?:\d+(?:\.\d+)?x)'
HOLDERS_PATTERN = r'(?i)(?:holder|hodler)s?[^\n]*?(\d[\d,]*\+?\s*(?:holder|hodler)?s?)'
MCAP_PATTERN = r'(?i)(?:mcap|market\s*cap)[^\n]*?\$\s*([\d,.]+\s*[kmb]?)'

@dataclass
class TokenContext:
    """Contextual information about a token mention."""
    address: str
    source: str
    confidence: float
    surrounding_text: str
    price_mentions: List[str]
    percentage_mentions: List[str]
    holder_mentions: List[str]
    mcap_mentions: List[str]
    mentioned_at: datetime

class EnhancedTokenParser:
    """Advanced token parser with context extraction."""
    
    def __init__(self) -> None:
        self.patterns = TOKEN_PATTERNS
        
    def extract_with_context(self, text: str) -> List[TokenContext]:
        """
        Extract tokens with surrounding context from text.
        """
        results = []
        
        # Process each pattern
        for pattern in self.patterns:
            for match in re.finditer(pattern.pattern, text, re.IGNORECASE):
                address = match.group(pattern.group_index)
                
                # Get surrounding text (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                surrounding_text = text[start:end]
                
                # Extract contextual information
                context = TokenContext(
                    address=address,
                    source=pattern.name,
                    confidence=pattern.confidence,
                    surrounding_text=surrounding_text,
                    price_mentions=re.findall(PRICE_PATTERN, surrounding_text),
                    percentage_mentions=re.findall(PERCENTAGE_PATTERN, surrounding_text),
                    holder_mentions=re.findall(HOLDERS_PATTERN, surrounding_text),
                    mcap_mentions=re.findall(MCAP_PATTERN, surrounding_text),
                    mentioned_at=datetime.utcnow()
                )
                
                results.append(context)
                
        return results
        
    def filter_duplicates(self, contexts: List[TokenContext]) -> List[TokenContext]:
        """
        Filter duplicate token mentions, keeping the ones with highest confidence
        and most context.
        """
        # Group by address
        by_address = {}
        for ctx in contexts:
            if ctx.address not in by_address or \
               ctx.confidence > by_address[ctx.address].confidence or \
               (ctx.confidence == by_address[ctx.address].confidence and \
                len(self._get_context_points(ctx)) > \
                len(self._get_context_points(by_address[ctx.address]))):
                by_address[ctx.address] = ctx
                
        return list(by_address.values())
        
    def _get_context_points(self, ctx: TokenContext) -> List[str]:
        """Get all context points from a TokenContext."""
        return [
            *ctx.price_mentions,
            *ctx.percentage_mentions,
            *ctx.holder_mentions,
            *ctx.mcap_mentions
        ]
        
    def get_validated_matches(self, text: str, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Get validated token matches from text.
        
        Args:
            text: Text to search for tokens
            min_confidence: Minimum confidence threshold (default: 0.7)
            
        Returns:
            List of validated token matches with address and metadata
        """
        contexts = self.extract_with_context(text)
        filtered = self.filter_duplicates(contexts)
        
        # Convert to simple dict format and filter by confidence
        return [
            {
                "address": ctx.address,
                "confidence": ctx.confidence,
                "source": ctx.source,
                "context": {
                    "price": ctx.price_mentions[0] if ctx.price_mentions else None,
                    "percentage": ctx.percentage_mentions[0] if ctx.percentage_mentions else None,
                    "holders": ctx.holder_mentions[0] if ctx.holder_mentions else None,
                    "mcap": ctx.mcap_mentions[0] if ctx.mcap_mentions else None,
                }
            }
            for ctx in filtered
            if ctx.confidence >= min_confidence
        ]
        
    def analyze_sentiment(self, ctx: TokenContext) -> float:
        """
        Analyze the sentiment of token mention context.
        Returns a score between -1.0 (very negative) and 1.0 (very positive).
        """
        text = ctx.surrounding_text.lower()
        
        # Positive indicators
        positive = sum(1 for word in [
            "moon", "gem", "pump", "bullish", "ape", "fomo",
            "launch", "early", "rocket", "next", "potential"
        ] if word in text)
        
        # Negative indicators
        negative = sum(1 for word in [
            "rug", "scam", "dump", "bearish", "shit",
            "fake", "honeypot", "avoid", "suspicious"
        ] if word in text)
        
        # Calculate sentiment
        total = positive + negative
        if total == 0:
            return 0.0
            
        return (positive - negative) / total

class PatternDetector:
    """Detect token patterns in text and price data."""
    
    def __init__(self) -> None:
        """Initialize the pattern detector."""
        self.token_patterns = TOKEN_PATTERNS
        self.compiled_patterns = {
            pattern.name: re.compile(pattern.pattern)
            for pattern in self.token_patterns
        }
    
    def extract_tokens(self, text: str) -> List[Dict[str, Any]]:
        """Extract token addresses from text with confidence scores."""
        results = []
        for pattern in self.token_patterns:
            matches = re.findall(pattern.pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # If we have multiple groups, use the specified group
                    token = match[pattern.group_index - 1] if len(match) >= pattern.group_index else match[0]
                else:
                    # Single group match
                    token = match
                
                # Add result if not already found with higher confidence
                if not any(r["address"] == token for r in results):
                    results.append({
                        "address": token,
                        "source": pattern.name,
                        "confidence": pattern.confidence
                    })
                
        return results
    
    async def detect_price_patterns(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in price data."""
        if not price_data or len(price_data) < 2:
            return {}
            
        patterns = {}
        
        # Get price changes
        prices = [item.get('price', 0) for item in price_data if item.get('price')]
        if not prices:
            return {}
            
        # Calculate basic metrics
        current_price = prices[-1]
        max_price = max(prices)
        min_price = min(prices)
        
        # Check for pump
        if len(prices) >= 3:
            recent_change = (prices[-1] / prices[-3] - 1) * 100 if prices[-3] > 0 else 0
            if recent_change > 20:
                patterns["recent_pump"] = recent_change
                
        # Check for all-time high
        if current_price >= max_price * 0.95:
            patterns["near_ath"] = True
            
        # Check for recovery from bottom
        if len(prices) >= 5 and min_price in prices[:-3]:
            bottom_idx = prices.index(min_price)
            if bottom_idx < len(prices) - 3:
                recovery = (current_price / min_price - 1) * 100
                if recovery > 50:
                    patterns["recovery"] = recovery
        
        return patterns
    
    async def detect_volume_patterns(self, volume_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in volume data."""
        if not volume_data or len(volume_data) < 2:
            return {}
            
        patterns = {}
        
        # Get volumes
        volumes = [item.get('volume', 0) for item in volume_data if item.get('volume')]
        if not volumes:
            return {}
            
        # Calculate basic metrics
        current_volume = volumes[-1]
        avg_volume = sum(volumes) / len(volumes)
        
        # Check for volume spike
        if current_volume > avg_volume * 3:
            patterns["volume_spike"] = current_volume / avg_volume
            
        # Check for consistent volume growth
        if len(volumes) >= 3:
            if all(volumes[i] <= volumes[i+1] for i in range(len(volumes)-3, len(volumes)-1)):
                patterns["growing_volume"] = True
        
        return patterns
    
    async def detect_holder_patterns(self, holder_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in holder data."""
        if not holder_data or len(holder_data) < 2:
            return {}
            
        patterns = {}
        
        # Get holder counts
        holders = [item.get('count', 0) for item in holder_data if item.get('count')]
        if not holders:
            return {}
            
        # Calculate basic metrics
        current_holders = holders[-1]
        
        # Check for holder growth
        if len(holders) >= 3:
            growth_rate = (current_holders / holders[-3] - 1) * 100 if holders[-3] > 0 else 0
            if growth_rate > 30:
                patterns["rapid_holder_growth"] = growth_rate
                
        # Check for whale behavior if available
        if any('whales' in item for item in holder_data):
            whale_data = [item.get('whales', {}) for item in holder_data if 'whales' in item]
            if whale_data and all('buying' in item for item in whale_data):
                whale_buying = [item.get('buying', False) for item in whale_data]
                if all(whale_buying[-3:]):
                    patterns["whale_accumulation"] = True
        
        return patterns
    
    async def detect_sentiment_patterns(self, sentiment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in social sentiment data."""
        if not sentiment_data or len(sentiment_data) < 2:
            return {}
            
        patterns = {}
        
        # Get sentiment scores
        scores = [item.get('score', 0) for item in sentiment_data if 'score' in item]
        if not scores:
            return {}
            
        # Calculate basic metrics
        avg_sentiment = sum(scores) / len(scores)
        
        # Check for positive sentiment
        if avg_sentiment > 0.7:
            patterns["positive_sentiment"] = avg_sentiment
            
        # Check for improving sentiment
        if len(scores) >= 3:
            if all(scores[i] <= scores[i+1] for i in range(len(scores)-3, len(scores)-1)):
                patterns["improving_sentiment"] = True
        
        return patterns
