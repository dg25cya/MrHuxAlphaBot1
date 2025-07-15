"""Token scoring service for evaluating token safety and hype metrics."""
from typing import Dict, Any, List, Optional, Union, cast
import time

from loguru import logger
from prometheus_client import Counter, Histogram

from src.models.token_metrics import TokenMetrics
from src.utils.redis_cache import RedisCache
from src.core.services.risk_assessment import RiskAssessmentService
from src.core.services.trend_detector import TrendDetectorService
from src.utils.type_conversion import safe_float, safe_int

# Metrics
SCORE_CALCULATION_COUNT = Counter(
    'token_score_calculations_total',
    'Number of token score calculations',
    ['type', 'status']
)

SCORE_CALCULATION_TIME = Histogram(
    'token_score_calculation_seconds',
    'Time spent calculating token scores',
    ['type']
)

class TokenScore:
    """Token score result."""
    
    def __init__(
        self,
        safety_score: float,
        hype_score: float,
        risk_factors: List[str],
        verdict: str,
        confidence: float
    ):
        """Initialize token score."""
        self.safety_score = safety_score
        self.hype_score = hype_score
        self.risk_factors = risk_factors
        self.verdict = verdict
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary for caching."""
        return {
            'safety_score': self.safety_score,
            'hype_score': self.hype_score,
            'risk_factors': self.risk_factors,
            'verdict': self.verdict,
            'confidence': self.confidence
        }

class TokenScorer:
    """Service for calculating token scores."""
    
    def __init__(self) -> None:
        """Initialize token scorer."""
        self.risk_assessor = RiskAssessmentService()
        self.trend_detector = TrendDetectorService()
        self.cache = RedisCache(ttl_seconds=300)  # 5-minute cache
        
        # Scoring weights
        self.weights = {
            "safety": {
                "mint": 0.3,
                "liquidity": 0.3,
                "audit": 0.2,
                "tax": 0.1,
                "holder_concentration": 0.1
            },
            "hype": {
                "volume_growth": 0.3,
                "holder_growth": 0.2,
                "buy_sell_ratio": 0.2,
                "whale_activity": 0.2,
                "social_momentum": 0.1
            }
        }
        
        # Thresholds for verdicts
        self.thresholds = {
            "high": {
                "safety": 80,
                "hype": 70,
                "combined": 75
            },
            "medium": {
                "safety": 60,
                "hype": 50,
                "combined": 55
            }
        }

    async def get_token_score(self, token_address: str, metrics: TokenMetrics) -> TokenScore:
        """Calculate and return token score."""
        return await self.calculate_token_score(token_address, metrics)

    async def calculate_token_score(self, token_address: str, metrics: TokenMetrics) -> TokenScore:
        """Calculate comprehensive token score."""
        # Try cache first
        cached = await self.cache.get(token_address)
        if cached:
            return TokenScore(**cached)

        start = time.time()
        try:
            # Calculate component scores
            safety_score = await self._calculate_safety_score(token_address)
            hype_score = await self._calculate_hype_score(token_address, metrics)
              # Collect risk factors from individual checks
            risk_factors = []
            if not await self.risk_assessor.is_mint_disabled(token_address):
                risk_factors.append("Mint authority enabled")
            
            confidence = self._calculate_confidence(safety_score, hype_score)
            
            # Calculate combined score and verdict
            combined_score = (safety_score + hype_score) / 2
            verdict = self._get_verdict(combined_score, safety_score, hype_score)
            
            # Create score object
            score = TokenScore(
                safety_score=safety_score,
                hype_score=hype_score,
                risk_factors=risk_factors,
                verdict=verdict,
                confidence=confidence
            )
            
            # Cache result
            await self.cache.set(token_address, score.to_dict())
            
            SCORE_CALCULATION_COUNT.labels(type='total', status='success').inc()
            return score
            
        except Exception as e:
            logger.error(f"Error calculating token score for {token_address}: {str(e)}")
            SCORE_CALCULATION_COUNT.labels(type='total', status='error').inc()
            raise
        finally:
            SCORE_CALCULATION_TIME.labels('total').observe(time.time() - start)

    async def _calculate_safety_score(self, token_address: str) -> float:
        """Calculate safety score component."""
        with SCORE_CALCULATION_TIME.labels('safety').time():
            try:                # Get risk assessment data from individual checks
                mint_disabled = await self.risk_assessor.is_mint_disabled(token_address)
                security_score = await self.risk_assessor.rug_client.get_security_score(token_address)
                
                scores = {
                    "mint": 100.0 if mint_disabled else 0.0,
                    "liquidity": security_score.liquidity_score,
                    "audit": 100.0 if security_score.is_contract_verified else 0.0,
                    "tax": 100.0 if security_score.buy_tax <= 0.05 and security_score.sell_tax <= 0.05 else 0.0,
                    "holder_concentration": 100.0 - (security_score.top_holders_percent or 0.0)
                }
                
                # Calculate weighted score
                safety_score = sum(
                    scores[metric] * self.weights["safety"][metric]
                    for metric in scores
                )
                
                SCORE_CALCULATION_COUNT.labels(type='safety', status='success').inc()
                return min(100, safety_score * 100)  # Convert to 0-100 scale
                
            except Exception as e:
                logger.error(f"Error calculating safety score for {token_address}: {str(e)}")
                SCORE_CALCULATION_COUNT.labels(type='safety', status='error').inc()
                return 0

    async def _calculate_hype_score(self, token_address: str, metrics: TokenMetrics) -> float:
        """Calculate hype score component."""
        with SCORE_CALCULATION_TIME.labels('hype').time():
            try:                # Convert metrics to appropriate types
                volume_24h = safe_float(metrics.volume_24h)
                holders = safe_int(metrics.holder_count)
                buys = safe_float(metrics.buy_count_24h)
                sells = safe_float(metrics.sell_count_24h)
                
                # Calculate individual metrics
                volume_growth = await self.trend_detector.analyze_volume_trend(token_address, volume_24h)
                holder_growth = await self.trend_detector.analyze_holder_trend(token_address, holders)
                buy_sell_ratio = buys / max(sells, 1.0)
                
                whale_activity = await self.trend_detector.analyze_whale_activity(token_address)
                social_momentum = await self.trend_detector.analyze_social_trend(token_address)
                
                # Score individual components
                hype_metrics = {
                    "volume_growth": min(100, volume_growth * 100),
                    "holder_growth": min(100, holder_growth * 100),
                    "buy_sell_ratio": min(100, buy_sell_ratio * 50),
                    "whale_activity": min(100, whale_activity * 100),
                    "social_momentum": min(100, social_momentum * 100)
                }
                
                # Calculate weighted score
                hype_score = sum(
                    hype_metrics[metric] * self.weights["hype"][metric]
                    for metric in hype_metrics
                )
                
                SCORE_CALCULATION_COUNT.labels(type='hype', status='success').inc()
                return min(100, hype_score)
                
            except Exception as e:
                logger.error(f"Error calculating hype score for {token_address}: {str(e)}")
                SCORE_CALCULATION_COUNT.labels(type='hype', status='error').inc()
                return 0

    def _calculate_confidence(self, safety_score: float, hype_score: float) -> float:
        """Calculate confidence score based on component scores."""
        # Higher confidence when scores are more balanced
        score_diff = abs(safety_score - hype_score)
        base_confidence = max(0, 1 - (score_diff / 100))
        
        # Higher confidence with higher scores
        avg_score = (safety_score + hype_score) / 2
        score_confidence = avg_score / 100
        
        return min(1.0, (base_confidence * 0.6) + (score_confidence * 0.4))

    def _get_verdict(self, combined_score: float, safety_score: float, hype_score: float) -> str:
        """Get final verdict based on component scores."""
        # Automatic red flags
        if safety_score < 30:
            return "AVOID ❌"
            
        if combined_score >= self.thresholds["high"]["combined"] and \
           safety_score >= self.thresholds["high"]["safety"] and \
           hype_score >= self.thresholds["high"]["hype"]:
            return "HOT BUY 🔥"
            
        if combined_score >= self.thresholds["medium"]["combined"] and \
           safety_score >= self.thresholds["medium"]["safety"] and \
           hype_score >= self.thresholds["medium"]["hype"]:
            return "WATCH 👀"
            
        return "CAUTION ⚠️"

    def _score_mint_status(self, mint_data: Dict[str, Any]) -> float:
        """Score mint authorization status."""
        if mint_data.get("revoked", False):
            return 1.0
        return 0.0

    def _score_liquidity(self, liquidity_data: Dict[str, Any]) -> float:
        """Score liquidity factors."""
        score = 0.0
        if liquidity_data.get("is_locked", False):
            score += 0.6
        
        # Score lock duration
        lock_days = liquidity_data.get("lock_duration_days", 0)
        score += min(0.4, lock_days / 365)  # Max bonus for 1 year lock
        
        return min(1.0, score)

    def _score_audit(self, audit_data: Dict[str, Any]) -> float:
        """Score audit status."""
        score = 0.0
        if audit_data.get("audited", False):
            score += 0.7
            if audit_data.get("audit_passed", False):
                score += 0.3
        return score

    def _score_tax(self, tax_data: Dict[str, Any]) -> float:
        """Score tax configuration."""
        buy_tax = tax_data.get("buy_tax", 100)
        sell_tax = tax_data.get("sell_tax", 100)
        
        # Score inversely - lower tax is better
        buy_score = max(0, 1 - (buy_tax / 20))  # Max acceptable tax 20%
        sell_score = max(0, 1 - (sell_tax / 20))
        
        return (buy_score + sell_score) / 2

    def _score_holder_concentration(self, holder_data: Dict[str, Any]) -> float:
        """Score holder concentration."""
        top_10_percent = holder_data.get("top_10_percent", 100)
        return max(0, 1 - (top_10_percent / 50))  # Penalize if top 10 hold >50%
