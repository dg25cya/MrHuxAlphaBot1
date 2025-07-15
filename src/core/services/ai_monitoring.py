"""AI-powered monitoring and analysis service."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import re
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest
from textblob import TextBlob
# import torch  # DISABLED for free hosting
# from transformers import pipeline  # DISABLED for free hosting

from src.config.settings import get_settings
from src.models.monitored_source import MonitoredSource, TokenTrendType
from src.utils.exceptions import AIServiceError
from src.core.services.output_service import OutputService

settings = get_settings()


@dataclass
class MessageAnalysis:
    """Container for message analysis results."""
    spam_score: float
    sentiment_score: float
    trends: List[TokenTrendType]
    anomaly_score: float
    patterns: List[str]
    tokens: Set[str]
    confidence: float
    metadata: Dict[str, Any]


class AICache:
    """Cache manager for AI analysis results."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600) -> None:
        """Initialize cache with max size and TTL."""
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired."""
        if key not in self.cache:
            return None
            
        timestamp = self.timestamps.get(key)
        if timestamp and (datetime.now() - timestamp).seconds > self.ttl:
            self.remove(key)
            return None
            
        return self.cache[key]
        
    def set(self, key: str, value: Any) -> None:
        """Add item to cache with timestamp."""
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest = min(self.timestamps.items(), key=lambda x: x[1])[0]
            self.remove(oldest)
            
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        
    def remove(self, key: str) -> None:
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)


class AIMonitoringService:
    """AI-powered monitoring service for enhanced token detection and analysis. (DISABLED for free hosting)"""

    def __init__(self, output_service: OutputService) -> None:
        """Initialize AI monitoring service."""
        self.output_service = output_service
        
        # Initialize text processing
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english'
        )
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            random_state=42
        )
        
        # Initialize message cache
        self.message_cache = []
        self.max_cache_size = settings.max_cache_size
        
        # Initialize sentiment model
        # self.sentiment_model = None  # DISABLED
        # if torch.cuda.is_available():
        #     try:
        #         self.sentiment_model = pipeline(
        #             task="sentiment-analysis",
        #             model="finiteautomata/bertweet-base-sentiment-analysis",
        #             device=0
        #         )
        #     except Exception as e:
        #         logger.warning(f"Failed to load GPU sentiment model: {e}")
        logger.warning("Advanced AI/ML (torch/transformers) is disabled for free hosting. Only TextBlob is available.")
                
    async def analyze_message(
        self, 
        message: str, 
        source: MonitoredSource
    ) -> Tuple[bool, MessageAnalysis]:
        """Analyze a message using AI/ML techniques."""
        try:
            message = message.strip()
            if len(message) < 10:
                return False, MessageAnalysis(
                    spam_score=1.0,
                    sentiment_score=0.0,
                    trends=[],
                    anomaly_score=0.0,
                    patterns=[],
                    tokens=set(),
                    confidence=0.0,
                    metadata={}
                )

            # Cache message for anomaly detection
            self.message_cache.append(message)
            if len(self.message_cache) > self.max_cache_size:
                self.message_cache.pop(0)

            # Perform analysis
            analysis = MessageAnalysis(
                spam_score=await self._check_spam(message),
                sentiment_score=await self._analyze_sentiment(message),
                trends=await self._detect_trends(message),
                anomaly_score=await self._detect_anomalies(message),
                patterns=await self._extract_patterns(message),
                tokens=set(await self._extract_potential_tokens(message)),
                confidence=0.0,
                metadata={}
            )

            # Calculate confidence
            analysis.confidence = self._calculate_confidence(analysis)
            
            return analysis.confidence >= settings.min_confidence_threshold, analysis
            
        except Exception as e:
            logger.exception(f"Error analyzing message: {e}")
            raise AIServiceError(f"Message analysis failed: {str(e)}")
            
    def _calculate_confidence(self, analysis: MessageAnalysis) -> float:
        """Calculate overall confidence score."""
        weights = {
            "spam": 0.3,
            "sentiment": 0.2,
            "trends": 0.2,
            "anomaly": 0.2,
            "patterns": 0.1
        }
        
        scores = {
            "spam": 1.0 - analysis.spam_score,
            "sentiment": abs(analysis.sentiment_score),
            "trends": min(len(analysis.trends) / 3, 1.0),
            "anomaly": 1.0 - analysis.anomaly_score,
            "patterns": min(len(analysis.patterns) / 5, 1.0)
        }
        
        return sum(weights[k] * scores[k] for k in weights)
            
    async def _check_spam(self, message: str) -> float:
        """Check if message is spam using ML techniques."""
        try:
            # Need at least 10 messages for meaningful anomaly detection
            if len(self.message_cache) < 10:
                return 0.5
            
            # Vectorize all messages
            vectors = self.vectorizer.fit_transform(self.message_cache)
            dense_vectors = vectors.toarray()
            
            # Use isolation forest for anomaly detection
            scores = self.anomaly_detector.fit_predict(dense_vectors)
            current_score = scores[-1]  # Score for the current message
            
            # Convert to probability (0 = likely spam, 1 = likely legitimate)
            return 1.0 / (1.0 + np.exp(-current_score))
            
        except Exception as e:
            logger.error(f"Error in spam detection: {e}")
            return 0.5  # Neutral score on error

    async def _analyze_sentiment(self, message: str) -> float:
        """Analyze message sentiment (TextBlob only)."""
        try:
            blob = TextBlob(message)
            score = float(blob.sentiment.polarity)
            return score
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return 0.0  # Neutral sentiment on error

    async def _detect_trends(self, message: str) -> List[TokenTrendType]:
        """Detect token-related trends in message."""
        trends = []
        
        # Price trends
        if any(word in message.lower() for word in ["price", "pump", "dump", "moon", "dip"]):
            trends.append(TokenTrendType.PRICE)
            
        # Volume trends    
        if any(word in message.lower() for word in ["volume", "liquidity", "trading"]):
            trends.append(TokenTrendType.VOLUME)
            
        # Holder trends
        if any(word in message.lower() for word in ["holders", "holding", "hodl"]):
            trends.append(TokenTrendType.HOLDERS)
            
        # Social trends
        if any(word in message.lower() for word in ["trending", "viral", "community"]):
            trends.append(TokenTrendType.SOCIAL)

        return trends

    async def _detect_anomalies(self, message: str) -> float:
        """Detect anomalous messages using isolation forest."""
        try:
            # Add to message cache
            self._message_cache.append(message)
            
            # Keep cache size reasonable
            if len(self._message_cache) > 1000:
                self._message_cache.pop(0)
                
            # Need minimum samples for anomaly detection
            if len(self._message_cache) < 10:
                return 0.5
                
            # Convert messages to feature vectors    
            vectors = self.vectorizer.fit_transform(self._message_cache)
            
            # Detect anomalies
            scores = self.anomaly_detector.fit_predict(vectors.toarray())
            
            # Convert prediction to anomaly score for latest message
            score = 1.0 if scores[-1] == -1 else 0.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return 0.5

    async def _extract_patterns(self, message: str) -> List[str]:
        """Extract recurring patterns that might indicate token discussion."""
        patterns = []
        
        try:
            # Split into words
            words = message.lower().split()
            
            # Look for known patterns
            for pattern, count in self._pattern_cache.items():
                if pattern in message.lower():
                    patterns.append(pattern)
                    self._pattern_cache[pattern] += 1
                    
            # Extract new patterns (pairs of words)
            for i in range(len(words) - 1):
                pattern = f"{words[i]} {words[i+1]}"
                if pattern in self._pattern_cache:
                    self._pattern_cache[pattern] += 1
                else:
                    self._pattern_cache[pattern] = 1
                    
            # Clean up pattern cache
            if len(self._pattern_cache) > 1000:
                # Remove least common patterns
                sorted_patterns = sorted(
                    self._pattern_cache.items(),
                    key=lambda x: x[1]
                )
                self._pattern_cache = dict(sorted_patterns[-1000:])
                
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return patterns

    async def _extract_potential_tokens(self, message: str) -> List[Dict[str, Any]]:
        """Extract potential token mentions with context."""
        tokens = []
        
        try:
            # Look for token address patterns
            address_pattern = r"0x[a-fA-F0-9]{40}"
            matches = re.findall(address_pattern, message)
            
            for addr in matches:
                context = self._get_surrounding_context(message, addr)
                tokens.append({
                    "address": addr,
                    "context": context,
                    "confidence": 0.9  # High confidence for address matches
                })
                
            # Look for token symbols
            symbol_pattern = r"\$[A-Z]{2,10}"
            matches = re.findall(symbol_pattern, message)
            
            for symbol in matches:
                context = self._get_surrounding_context(message, symbol)
                tokens.append({
                    "symbol": symbol[1:],  # Remove $ prefix
                    "context": context,
                    "confidence": 0.7  # Medium confidence for symbol matches
                })
                
            return tokens
            
        except Exception as e:
            logger.error(f"Error extracting tokens: {e}")
            return tokens

    def _get_surrounding_context(self, message: str, target: str, window: int = 50) -> str:
        """Get text surrounding a target string."""
        try:
            start = max(0, message.find(target) - window)
            end = min(len(message), message.find(target) + len(target) + window)
            return message[start:end].strip()
        except Exception as e:
            return ""

    async def _update_patterns(self, message: str, analysis: Dict[str, Any]):
        """Update pattern learning based on message analysis."""
        if analysis["confidence"] > 0.8:
            patterns = await self._extract_patterns(message)
            for pattern in patterns:
                self._pattern_cache[pattern] = self._pattern_cache.get(pattern, 0) + 2

    async def get_pattern_insights(self) -> Dict[str, Any]:
        """Get insights about learned patterns."""
        return {
            "top_patterns": sorted(
                self._pattern_cache.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "pattern_count": len(self._pattern_cache),
            "total_occurrences": sum(self._pattern_cache.values())
        }
