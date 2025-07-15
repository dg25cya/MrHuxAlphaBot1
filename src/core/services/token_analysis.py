"""Advanced token analysis and pattern detection service."""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from loguru import logger
from prometheus_client import Counter, Histogram, REGISTRY

from ...utils.sentiment import SentimentAnalyzer
from ...config.settings import get_settings
from ...models.token import Token

settings = get_settings()

# Metric wrapper classes
class SafeCounter:
    """Thread-safe counter with automatic initialization."""
    def __init__(self, name: str, description: str, labels: List[str] = None) -> None:
        try:
            self._counter = Counter(name, description, labelnames=labels if labels else [])
        except ValueError:  # Already exists
            self._counter = REGISTRY._names_to_collectors[name]
    
    def inc(self, amount: float = 1.0, **labels) -> None:
        """Increment counter with optional labels."""
        try:
            if labels:
                counter = self._counter.labels(**labels)
                counter.inc(amount)
            else:
                self._counter.inc(amount)
        except Exception as e:
            logger.error(f"Error incrementing counter {self._counter._name if hasattr(self._counter, '_name') else 'unknown'}: {e}")

class SafeHistogram:
    """Thread-safe histogram with automatic initialization."""
    def __init__(self, name: str, description: str, buckets: list[float]) -> None:
        try:
            self._histogram = Histogram(name, description, buckets=buckets)
        except ValueError:  # Already exists
            self._histogram = REGISTRY._names_to_collectors[name]
    
    def observe(self, value: float) -> None:
        """Record an observation."""
        try:
            if hasattr(self._histogram, 'observe'):
                self._histogram.observe(value)
            else:
                logger.error("Histogram object does not have observe method")
        except Exception as e:
            logger.error(f"Error recording observation for {self._histogram._name if hasattr(self._histogram, '_name') else 'unknown'}: {e}")

# Initialize metrics with wrapper classes
PATTERN_MATCHES = SafeCounter(
    'token_pattern_matches_total',
    'Number of token pattern matches by type',
    ['pattern_type']
)

SENTIMENT_SCORES = SafeHistogram(
    'token_sentiment_scores',
    'Distribution of token sentiment scores',
    buckets=[-1.0, -0.5, 0.0, 0.5, 1.0]
)

@dataclass
class TokenContext:
    """Context information for a token mention."""
    text: str
    timestamp: datetime
    channel_id: int
    message_id: int
    token: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume: Optional[float] = None
    hype_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    hype_indicators: Dict[str, float] = field(default_factory=dict)
    patterns_detected: List[str] = field(default_factory=list)
    risk_indicators: Dict[str, float] = field(default_factory=dict)

class TokenAnalysisService:
    """Service for advanced token analysis and pattern detection."""
    
    # Prometheus metrics for token analysis
    TOKENS_ANALYZED = Counter('token_analyzer_processed_total', 'Total number of tokens analyzed by the analyzer')
    ANALYSIS_TIME = Histogram('token_analyzer_processing_seconds', 'Time spent analyzing tokens by the analyzer')
    ANALYSIS_ERRORS = Counter('token_analyzer_errors_total', 'Total number of analyzer errors')
    
    def __init__(self) -> None:
        """Initialize the token analysis service."""
        # Initialize API clients
        from ...api.clients.birdeye import BirdeyeClient
        from ...api.clients.dexscreener import DexscreenerClient
        from ...api.clients.social_data import SocialDataClient
        
        self.birdeye_client = BirdeyeClient()
        self.dexscreener_client = DexscreenerClient()
        self.social_client = SocialDataClient()
        
        # Sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Common token-related keywords
        self.bullish_words = {
            'moon', 'pump', 'bull', 'bullish', 'gem', 'early',
            'launch', 'presale', 'potential', 'massive', 'huge'
        }
        self.bearish_words = {
            'dump', 'bear', 'bearish', 'rug', 'scam', 'fake',
            'dead', 'sell', 'selling', 'dropped'
        }

        # Advanced token patterns
        self.whale_patterns = [
            r'whale[s]?\s+buy',
            r'(\d+)[kK]\+?\s+(buy|purchase)',
            r'big\s+(buyer|purchase|bag)',
            r'accumulation'
        ]
        
        self.momentum_patterns = [
            r'break(ing|s)?\s+(ath|high)',
            r'trend(ing)?\s+(up|higher)',
            r'(higher|rising)\s+lows?',
            r'volume\s+spike'
        ]

        self.time_patterns = [
            r'(\d+)\s*(min|minutes|mins)',
            r'(\d+)\s*(hour|hours|hrs)',
            r'(\d+)\s*(day|days)',
            r'(soon|imminent|today|tomorrow)',
        ]
        
        self.risk_patterns = {
            'contract_risk': [
                r'mint\s+enabled',
                r'honeypot',
                r'high\s+tax',
                r'unlocked\s+lp'
            ],
            'market_risk': [
                r'low\s+liquidity',
                r'under\s+\$\d+k\s+mc',
                r'(no|zero)\s+utility'
            ]
        }
        
    async def get_token_momentum(self, token_address: str) -> Dict[str, Any]:
        """
        Get token momentum metrics including volume changes, price action, and social activity.
        
        Args:
            token_address: The token's contract address
            
        Returns:
            Dictionary containing momentum metrics
        """
        try:
            # Get token data from various sources
            birdeye_data = await self.birdeye_client.get_token_data(token_address)
            dex_data = await self.dexscreener_client.get_token_data(token_address)
            social_data = await self.social_client.get_token_mentions(token_address)
            
            # Calculate volume momentum
            volume_change_24h = 0
            if birdeye_data and "volume_24h" in birdeye_data:
                volume_24h = float(birdeye_data["volume_24h"])
                volume_change_24h = (
                    (volume_24h - birdeye_data.get("volume_24h_previous", 0)) /
                    birdeye_data.get("volume_24h_previous", 1)
                ) * 100 if birdeye_data.get("volume_24h_previous") else 0
            
            # Calculate price momentum
            price_change_24h = float(birdeye_data.get("price_change_24h", 0))
            price_change_1h = float(birdeye_data.get("price_change_1h", 0))
            
            # Calculate social momentum
            social_mentions_24h = len([
                m for m in social_data
                if (datetime.now() - m["timestamp"]).total_seconds() < 86400
            ]) if social_data else 0
            
            # Get trade metrics
            trades_24h = birdeye_data.get("trades_24h", 0)
            buy_pressure = birdeye_data.get("buy_count_24h", 0) / max(trades_24h, 1)
            
            momentum_score = self._calculate_momentum_score(
                volume_change_24h,
                price_change_24h,
                social_mentions_24h,
                buy_pressure
            )
            
            return {
                "momentum_score": momentum_score,
                "volume_change_24h": volume_change_24h,
                "price_change_24h": price_change_24h,
                "price_change_1h": price_change_1h,
                "social_mentions_24h": social_mentions_24h,
                "buy_pressure": buy_pressure,
                "trades_24h": trades_24h
            }
            
        except Exception as e:
            logger.error(f"Error getting token momentum for {token_address}: {str(e)}")
            return {
                "momentum_score": 0,
                "volume_change_24h": 0,
                "price_change_24h": 0,
                "price_change_1h": 0,
                "social_mentions_24h": 0,
                "buy_pressure": 0,
                "trades_24h": 0
            }
                
    def _calculate_momentum_score(
        self,
        volume_change: float,
        price_change: float,
        social_mentions: int,
        buy_pressure: float
    ) -> float:
        """Calculate overall momentum score from various metrics."""
        # Normalize metrics
        vol_score = min(max(volume_change / 100, 0), 1)  # Cap at 100% change
        price_score = min(max((price_change + 100) / 200, 0), 1)  # Normalize to 0-1
        social_score = min(social_mentions / 100, 1)  # Cap at 100 mentions
        pressure_score = buy_pressure  # Already 0-1
        
        # Weight the components
        weights = {
            "volume": 0.3,
            "price": 0.3,
            "social": 0.2,
            "pressure": 0.2
        }
        
        momentum_score = (
            vol_score * weights["volume"] +
            price_score * weights["price"] +
            social_score * weights["social"] +
            pressure_score * weights["pressure"]
        ) * 100  # Convert to 0-100 scale
        
        return round(momentum_score, 2)
        
        self.risk_patterns = {
            'contract_risk': [
                r'mint\s+enabled',
                r'honeypot',
                r'high\s+tax',
                r'unlocked\s+lp'
            ],
            'market_risk': [
                r'low\s+liquidity',
                r'under\s+\$\d+k\s+mc',
                r'(no|zero)\s+utility'
            ]
        }
        
        # Time-based patterns
        self.time_patterns = [
            r'(\d+)\s*(min|minutes|mins)',
            r'(\d+)\s*(hour|hours|hrs)',
            r'(\d+)\s*(day|days)',
            r'(soon|imminent|today|tomorrow)',
        ]
        
        # Initialize pattern counters
        self.pattern_counts = defaultdict(int)
        
        try:
            # Prometheus metrics
            self.TOKENS_ANALYZED = Counter('token_analyzer_processed_total', 'Total number of tokens analyzed by the analyzer')
            self.ANALYSIS_TIME = Histogram('token_analyzer_processing_seconds', 'Time spent analyzing tokens by the analyzer')
            self.ANALYSIS_ERRORS = Counter('token_analyzer_errors_total', 'Total number of analyzer errors')
        except Exception as e:
            logger.warning(f"Error initializing metrics: {e}")
            from prometheus_client import REGISTRY
            for metric in REGISTRY.collect():
                if metric.name == 'token_analyzer_processed_total':
                    self.TOKENS_ANALYZED = Counter('token_analyzer_processed_total', 'Total number of tokens analyzed by the analyzer', registry=None)
                if metric.name == 'token_analyzer_processing_seconds':
                    self.ANALYSIS_TIME = Histogram('token_analyzer_processing_seconds', 'Time spent analyzing tokens by the analyzer', registry=None)
                if metric.name == 'token_analyzer_errors_total':
                    self.ANALYSIS_ERRORS = Counter('token_analyzer_errors_total', 'Total number of analyzer errors', registry=None)
    
    async def analyze_token_mention(
        self,
        text: str,
        channel_id: int,
        message_id: int,
        token_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a token mention with context.
        
        Args:
            text: The message text containing the token mention
            channel_id: The Telegram channel ID
            message_id: The message ID
            token_address: Optional token address if already known
        
        Returns:
            TokenContext object with analysis results
        """
        try:
            # Extract token data and analyze it
            token_data = await self._extract_token_data(text, token_address)
            if not token_data:
                return {}

            # Validate token data
            is_valid = await self._validate_token_data(token_data)
            if not is_valid:
                logger.debug(f"Invalid token mention in message {message_id}")
                return {}

            # Detect patterns and analyze sentiment
            patterns = await self._detect_patterns(text)
            sentiment = await self._analyze_sentiment(text)
            risk_indicators = await self._analyze_risks(text, token_data)
            
            # Create context object
            context = TokenContext(
                text=text,
                timestamp=datetime.now(),
                channel_id=channel_id,
                message_id=message_id,
                token=token_data.get("token"),
                address=token_data.get("address"),
                price=token_data.get("price"),
                market_cap=token_data.get("market_cap"),
                volume=token_data.get("volume"),
                hype_score=await self._calculate_hype_score(text, patterns),
                sentiment_score=sentiment,
                hype_indicators=await self._get_hype_indicators(text, patterns),
                patterns_detected=patterns,
                risk_indicators=risk_indicators
            )

            self.TOKENS_ANALYZED.inc()
            SENTIMENT_SCORES.observe(sentiment)
            
            # Convert TokenContext to dict
            return {
                "token": context.token,
                "address": context.address,
                "price": context.price,
                "market_cap": context.market_cap,
                "volume": context.volume,
                "hype_score": context.hype_score,
                "sentiment_score": context.sentiment_score,
                "hype_indicators": context.hype_indicators,
                "patterns_detected": context.patterns_detected,
                "risk_indicators": context.risk_indicators,
                "score": self._calculate_final_score(context)
            }

        except Exception as e:
            logger.exception(f"Error analyzing token mention: {e}")
            self.ANALYSIS_ERRORS.inc()
            return {}
    
    async def _extract_token_data(self, text: str, token_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract token info from message text."""
        try:
            # Extract token address using regex patterns
            token_pattern = r'\$([A-Z0-9]+)'
            price_pattern = r'(\$[\d,.]+[KMB]?)'
            mcap_pattern = r'MC:?\s*\$?([\d,.]+[KMB]?)'
            volume_pattern = r'VOL:?\s*\$?([\d,.]+[KMB]?)'
            
            # Try to find token symbol/name first
            token_match = re.search(token_pattern, text)
            if not token_match and not token_address:
                return None
                
            # Extract price, mcap, volume
            price_match = re.search(price_pattern, text)
            mcap_match = re.search(mcap_pattern, text)
            volume_match = re.search(volume_pattern, text)
            
            return {
                "token": token_match.group(1) if token_match else None,
                "address": token_address,
                "price": self._parse_numeric_value(price_match.group(1)) if price_match else None,
                "market_cap": self._parse_numeric_value(mcap_match.group(1)) if mcap_match else None,
                "volume": self._parse_numeric_value(volume_match.group(1)) if volume_match else None,
            }
        except Exception as e:
            logger.error(f"Error extracting token data: {e}")
            return None

    def _parse_numeric_value(self, value: str) -> Optional[float]:
        """Parse numeric values with K/M/B suffixes."""
        try:
            value = value.replace('$', '').replace(',', '')
            multiplier = 1
            
            if value.endswith('K'):
                multiplier = 1_000
                value = value[:-1]
            elif value.endswith('M'):
                multiplier = 1_000_000
                value = value[:-1]
            elif value.endswith('B'):
                multiplier = 1_000_000_000
                value = value[:-1]
                
            return float(value) * multiplier
        except Exception as e:
            return None

    async def _validate_token_data(self, token_data: Dict[str, Any]) -> bool:
        """Validate the extracted token data."""
        return bool(token_data and (token_data.get("token") or token_data.get("address")))

    async def _detect_patterns(self, text: str) -> List[str]:
        """Detect various token patterns in text."""
        patterns = []
        text = text.lower()
        
        # Check whale patterns
        for pattern in self.whale_patterns:
            if re.search(pattern, text):
                patterns.append('whale_activity')
                PATTERN_MATCHES.inc(pattern_type='whale')
                break
                
        # Check momentum patterns
        for pattern in self.momentum_patterns:
            if re.search(pattern, text):
                patterns.append('momentum')
                PATTERN_MATCHES.inc(pattern_type='momentum')
                break
                
        # Check time patterns
        for pattern in self.time_patterns:
            if re.search(pattern, text):
                patterns.append('time_sensitive')
                PATTERN_MATCHES.inc(pattern_type='time')
                break
                
        return patterns
        
    async def _analyze_risks(self, text: str, token_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze various risk factors."""
        risks = {}
        text = text.lower()
        
        # Check contract risks
        contract_risk = 0.0
        for pattern in self.risk_patterns['contract_risk']:
            if re.search(pattern, text):
                contract_risk += 0.25  # Each risk factor adds 25%
        risks['contract_risk'] = min(contract_risk, 1.0)
        
        # Check market risks
        market_risk = 0.0
        for pattern in self.risk_patterns['market_risk']:
            if re.search(pattern, text):
                market_risk += 0.25
        risks['market_risk'] = min(market_risk, 1.0)
        
        # Additional risk checks based on token data
        if token_data.get('market_cap', 0) and token_data['market_cap'] < 50000:  # Less than $50k mcap
            risks['micro_cap_risk'] = 0.75
        elif token_data.get('market_cap', 0) and token_data['market_cap'] < 250000:  # Less than $250k mcap
            risks['micro_cap_risk'] = 0.25
            
        if token_data.get('volume', 0) and token_data['volume'] < 1000:  # Less than $1k volume
            risks['low_volume_risk'] = 0.75
            
        return risks

    async def _calculate_hype_score(self, text: str, patterns: List[str]) -> float:
        """Calculate a hype score based on message content and detected patterns."""
        try:
            # Base hype from keyword presence
            hype_words = ['moon', 'pump', 'rocket', 'gems', 'x', 'potential']
            base_score = sum(word.lower() in text.lower() for word in hype_words) / len(hype_words)
            
            # Boost score based on detected patterns
            pattern_boost = 0.0
            if 'whale_activity' in patterns:
                pattern_boost += 0.2
            if 'momentum' in patterns:
                pattern_boost += 0.2
            if 'time_sensitive' in patterns:
                pattern_boost += 0.1
                
            # Calculate final score with caps
            return min(base_score + pattern_boost, 1.0)
        except Exception as e:
            logger.error(f"Error calculating hype score: {e}")
            return 0.0
            
    async def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of token mention using sentiment analyzer.
        Returns score between -1.0 (negative) and 1.0 (positive).
        """
        try:
            # Get base sentiment from analyzer
            sentiment_result = await self.sentiment_analyzer.analyze(text)
            base_sentiment = sentiment_result.get("score", 0.0)
            
            # Add keyword-based sentiment
            text = text.lower()
            positive_count = sum(word in text for word in self.bullish_words)
            negative_count = sum(word in text for word in self.bearish_words)
            
            if positive_count + negative_count == 0:
                return base_sentiment
                
            keyword_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            
            # Combine scores with higher weight on base sentiment
            return 0.7 * base_sentiment + 0.3 * keyword_sentiment
        
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return 0.0

    async def _get_hype_indicators(self, text: str, patterns: List[str]) -> Dict[str, float]:
        """Get detailed hype indicators from text and patterns."""
        indicators = {}
        text = text.lower()
        
        # Social engagement indicators
        mentions = len(re.findall(r'@\w+', text))
        if mentions > 0:
            indicators['social_engagement'] = min(mentions * 0.2, 1.0)
            
        # Price action indicators
        if any(pattern in text for pattern in ['ath', 'breaking out', 'new high']):
            indicators['price_momentum'] = 0.8
            
        # Time sensitivity
        if 'time_sensitive' in patterns:
            indicators['urgency'] = 0.7
            
        # Whale activity
        if 'whale_activity' in patterns:
            indicators['whale_interest'] = 0.9
            
        # Volume activity
        volume_terms = ['volume', 'liquidity', 'trading']
        if any(term in text for term in volume_terms):
            indicators['volume_activity'] = 0.6
            
        return indicators
        
    def _calculate_final_score(self, context: TokenContext) -> float:
        """Calculate final token score based on all metrics."""
        try:
            base_score = 5.0  # Start with neutral score
            
            # Add/subtract based on sentiment (up to ±2.0)
            if context.sentiment_score is not None:
                base_score += context.sentiment_score * 2
            
            # Add based on hype (up to +2.0)
            if context.hype_score is not None:
                base_score += context.hype_score * 2
                
            # Subtract based on risks (up to -3.0)
            risk_penalty = 0
            for risk_type, risk_value in context.risk_indicators.items():
                if 'contract_risk' in risk_type:
                    risk_penalty += risk_value * 2
                elif 'market_risk' in risk_type:
                    risk_penalty += risk_value
                    
            base_score -= risk_penalty
            
            # Add pattern bonuses (up to +1.0)
            if len(context.patterns_detected) > 0:
                base_score += min(len(context.patterns_detected) * 0.25, 1.0)
            
            # Ensure score is between 0 and 10
            return max(0.0, min(10.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            return 5.0  # Return neutral score on error
