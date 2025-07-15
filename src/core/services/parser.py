"""Token parsing and analysis service."""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger
from prometheus_client import Counter, Histogram

from ...config.settings import get_settings
from .token_patterns import TokenPattern
from .token_analysis import TokenAnalysisService
from .image_processor import image_processor

settings = get_settings()

# Metrics
PARSE_TIME = Histogram(
    'token_parse_time_seconds',
    'Time spent parsing messages for tokens'
)

TOKENS_FOUND = Counter(
    'tokens_found_total',
    'Number of tokens found in messages',
    ['source', 'pattern']
)

PARSE_ERRORS = Counter(
    'token_parse_errors_total',
    'Number of errors encountered while parsing messages',
    ['source', 'error_type']
)

INVALID_ADDRESSES = Counter(
    'invalid_token_addresses_total',
    'Number of invalid token addresses found',
    ['source', 'pattern']
)

# Cache settings
MAX_CACHE_SIZE = 1000
CACHE_EXPIRY = 300  # 5 minutes


class TokenMatch:
    """Represents a token match found in text."""
    
    def __init__(self, address: str, pattern: str, confidence: float, context: str = ""):
        self.address = address
        self.pattern = pattern
        self.confidence = confidence
        self.context = context


class TokenParser:
    """Service for parsing and analyzing token mentions in messages."""
    
    def __init__(self) -> None:
        """Initialize the token parser."""
        self.analyzer = TokenAnalysisService()
        self._cache = {}
        self._cache_times = {}
        self._rate_limits = {}
        
        # Initialize patterns
        self._init_patterns()
        
    def _init_patterns(self) -> None:
        """Initialize token detection patterns."""
        self.patterns = [
            TokenPattern(
                name="solana_address",
                pattern=r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b',
                confidence=0.7
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
            )
        ]
    
    def _validate_address(self, address: str) -> bool:
        """Validate Solana token address format."""
        if not address or len(address) < 32 or len(address) > 44:
            return False
        return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))
        
    def _check_rate_limit(self, channel_id: int) -> bool:
        """Check if channel is rate limited."""
        current_time = datetime.now().timestamp()
        if channel_id in self._rate_limits:
            last_time, count = self._rate_limits[channel_id]
            if current_time - last_time < 60:  # 1 minute window
                if count >= 60:  # Max 60 messages per minute
                    return False
                self._rate_limits[channel_id] = (last_time, count + 1)
            else:
                self._rate_limits[channel_id] = (current_time, 1)
        else:
            self._rate_limits[channel_id] = (current_time, 1)
        return True

    async def process_image(self, image_url: str) -> List[Dict[str, Any]]:
        """
        Extract tokens from an image using OCR.
        
        Args:
            image_url: The URL of the image to process
            
        Returns:
            List of detected token data
        """
        try:
            # Download and process image
            if not image_url:
                return []
                
            # Get image data
            image_data = await image_processor.download_image(image_url)
            if not image_data:
                PARSE_ERRORS.labels(source="image", error_type="download_failed").inc()
                return []
                
            # Extract text with OCR
            regions = await image_processor.process_image(image_data)
            if not regions:
                return []
                
            tokens = []
            # Check each text region for token patterns
            for region in regions:
                # Skip low confidence results
                if region.confidence < 0.6:
                    continue
                    
                # Look for tokens in extracted text
                for pattern in self.patterns:
                    matches = pattern.find_matches(region.text)
                    for match in matches:
                        address = match["address"]
                        if self._validate_address(address):
                            tokens.append({
                                "address": address,
                                "source": "image",
                                "pattern": pattern.name,
                                "confidence": region.confidence * pattern.confidence,
                                "context": region.text
                            })
                        else:
                            INVALID_ADDRESSES.labels(
                                source="image", 
                                pattern=pattern.name
                            ).inc()
                            
            if tokens:
                TOKENS_FOUND.labels(source="image", pattern="ocr").inc(len(tokens))
                
            return tokens
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            PARSE_ERRORS.labels(source="image", error_type="processing_error").inc()
            return []
            
    async def parse_message(self, text: str, channel_id: Optional[int] = None, 
                          message_id: Optional[int] = None, image_urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Parse message for token mentions from text and attached images.
        """
        try:
            with PARSE_TIME.time():
                if not text and not image_urls:
                    return []
                    
                if channel_id and not self._check_rate_limit(channel_id):
                    logger.warning(f"Rate limit exceeded for channel {channel_id}")
                    return []
                    
                tokens = []
                
                # Process text content
                if text:
                    for pattern in self.patterns:
                        matches = pattern.find_matches(text)
                        for match in matches:
                            if self._validate_address(match["address"]):
                                tokens.append({
                                    "address": match["address"],
                                    "source": "text",
                                    "pattern": pattern.name,
                                    "confidence": pattern.confidence,
                                    "context": match.get("context", "")
                                })
                            else:
                                INVALID_ADDRESSES.labels(
                                    source="text", 
                                    pattern=pattern.name
                                ).inc()
                                
                # Process images if any
                if image_urls:
                    for url in image_urls:
                        image_tokens = await self.process_image(url)
                        tokens.extend(image_tokens)
                        
                # Remove duplicates while preserving order
                seen = set()
                unique_tokens = []
                for t in tokens:
                    addr = t["address"]
                    if addr not in seen:
                        seen.add(addr)
                        unique_tokens.append(t)
                        
                if unique_tokens:
                    TOKENS_FOUND.labels(source="total", pattern="all").inc(len(unique_tokens))
                    
                return unique_tokens
                
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            PARSE_ERRORS.labels(source="parser", error_type="general").inc()
            return []
