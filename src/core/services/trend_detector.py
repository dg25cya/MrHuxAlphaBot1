"""Service for detecting and analyzing token trends and momentum."""
import time

from loguru import logger
from prometheus_client import Counter, Histogram

from ...api.clients.birdeye import BirdeyeClient
from ...config.settings import get_settings

settings = get_settings()

# Metrics
TREND_ANALYSIS_TIME = Histogram(
    'trend_analysis_duration_seconds',
    'Time spent analyzing trends',
    ['analysis_type']
)

TREND_DETECTION_ERRORS = Counter(
    'trend_detection_errors_total',
    'Number of trend detection errors by type',
    ['error_type']
)

class TrendDetectorService:
    """Service for analyzing token market trends and social metrics."""

    def __init__(self) -> None:
        """Initialize the trend detector with required clients."""
        self.birdeye_client = BirdeyeClient()
        
        # Analysis thresholds
        self.thresholds = {
            "volume": {
                "growth": 2.0,  # 200% growth for high activity
                "minimal": 5000.0,  # $5k minimum for valid volume
            },
            "holders": {
                "growth": 0.2,  # 20% growth
                "minimal": 100,  # Minimum holders
            },
            "whales": {
                "min_tx": 10000.0,  # $10k USD min for whale tx
                "impact": 0.05,  # 5% of 24h volume
            },
            "social": {
                "mentions": 5,  # Minimum mentions
                "sentiment": 0.6,  # Positive sentiment threshold
            }
        }

    async def calculate_volume_growth(self, token_address: str, current_volume: float) -> float:
        """Calculate volume growth rate over time."""
        try:
            with TREND_ANALYSIS_TIME.labels('volume_growth').time():
                # Get historical price data
                prev_day = await self.birdeye_client.get_market_activity(token_address)
                prev_volume = float(prev_day.get('volume_buy_usd', 0)) + float(prev_day.get('volume_sell_usd', 0))
                
                if prev_volume == 0:
                    return float(current_volume > 0)  # Return 1.0 if there's any current volume
                
                growth_rate = (float(current_volume) - prev_volume) / prev_volume
                return max(0.0, growth_rate)  # Don't return negative growth

        except Exception as e:
            logger.error(f"Error calculating volume growth for {token_address}: {e}")
            TREND_DETECTION_ERRORS.labels('volume_growth').inc()
            return 0.0

    async def calculate_holder_growth(self, token_address: str, current_holders: int) -> float:
        """Calculate holder growth rate."""
        try:
            with TREND_ANALYSIS_TIME.labels('holder_growth').time():
                # Get historical holder data
                prev_holder_info = await self.birdeye_client.get_holder_info(token_address)
                prev_holders = prev_holder_info.get('holder_count', current_holders)
                
                if prev_holders == 0:
                    return float(current_holders > 0)  # Return 1.0 if there are any current holders
                
                growth_rate = (current_holders - prev_holders) / prev_holders
                return max(0.0, float(growth_rate))  # Don't return negative growth

        except Exception as e:
            logger.error(f"Error calculating holder growth for {token_address}: {e}")
            TREND_DETECTION_ERRORS.labels('holder_growth').inc()
            return 0.0

    async def analyze_volume_trend(self, token_address: str, current_volume: float) -> float:
        """Analyze volume trend and return normalized score 0-1."""
        try:
            with TREND_ANALYSIS_TIME.labels('volume').time():
                if current_volume < self.thresholds["volume"]["minimal"]:
                    return 0.0
                    
                prev_volume = await self.birdeye_client.get_previous_volume(token_address)
                if not prev_volume:
                    return 0.1 if current_volume > self.thresholds["volume"]["minimal"] else 0.0
                
                growth = (current_volume - prev_volume) / prev_volume
                return min(1.0, growth / self.thresholds["volume"]["growth"])
                
        except Exception as e:
            logger.error(f"Volume trend analysis error for {token_address}: {str(e)}")
            TREND_DETECTION_ERRORS.labels(error_type="volume").inc()
            return 0.0

    async def analyze_holder_trend(self, token_address: str, current_holders: int) -> float:
        """Analyze holder growth trend and return normalized score 0-1."""
        try:
            with TREND_ANALYSIS_TIME.labels('holders').time():
                if current_holders < self.thresholds["holders"]["minimal"]:
                    return 0.0
                    
                prev_holders = await self.birdeye_client.get_previous_holders(token_address)
                if not prev_holders:
                    return 0.1 if current_holders > self.thresholds["holders"]["minimal"] else 0.0
                
                growth = (current_holders - prev_holders) / prev_holders
                return min(1.0, growth / self.thresholds["holders"]["growth"])
                
        except Exception as e:
            logger.error(f"Holder trend analysis error for {token_address}: {str(e)}")
            TREND_DETECTION_ERRORS.labels(error_type="holders").inc()
            return 0.0

    async def analyze_whale_activity(self, token_address: str) -> float:
        """Analyze whale activity and return normalized score 0-1."""
        try:
            with TREND_ANALYSIS_TIME.labels('whales').time():
                whale_txs = await self.birdeye_client.get_whale_transactions(
                    token_address,
                    min_amount=self.thresholds["whales"]["min_tx"]
                )
                
                if not whale_txs:
                    return 0.0
                    
                total_volume = await self.birdeye_client.get_24h_volume(token_address)
                if not total_volume:
                    return 0.0
                    
                whale_volume = sum(tx["amount_usd"] for tx in whale_txs)
                impact = whale_volume / total_volume
                
                return min(1.0, impact / self.thresholds["whales"]["impact"])
                
        except Exception as e:
            logger.error(f"Whale activity analysis error for {token_address}: {str(e)}")
            TREND_DETECTION_ERRORS.labels(error_type="whales").inc()
            return 0.0

    async def analyze_social_trend(self, token_address: str) -> float:
        """Analyze social media momentum and return normalized score 0-1."""
        try:
            with TREND_ANALYSIS_TIME.labels('social').time():
                mentions = await self.birdeye_client.get_social_mentions(token_address)
                if not mentions or len(mentions) < self.thresholds["social"]["mentions"]:
                    return 0.0
                    
                sentiment = await self.birdeye_client.get_social_sentiment(token_address)
                if not sentiment:
                    return 0.0
                    
                # Weight: 60% mention count, 40% sentiment
                mention_score = min(1.0, len(mentions) / (self.thresholds["social"]["mentions"] * 2))
                sentiment_score = sentiment if sentiment > self.thresholds["social"]["sentiment"] else 0
                
                return (mention_score * 0.6) + (sentiment_score * 0.4)
                
        except Exception as e:
            logger.error(f"Social trend analysis error for {token_address}: {str(e)}")
            TREND_DETECTION_ERRORS.labels(error_type="social").inc()
            return 0.0
