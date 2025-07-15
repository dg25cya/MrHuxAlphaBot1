"""Service for assessing token risks and safety metrics."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
import asyncio
from datetime import datetime, timedelta

from loguru import logger
from prometheus_client import Counter, Gauge, Histogram

from src.api.clients.rugcheck import RugcheckClient
from src.api.clients.birdeye import BirdeyeClient
from src.api.clients.dexscreener import DexscreenerClient
from src.config.settings import get_settings
from src.utils.exceptions import RiskAssessmentError
from src.utils.decimal import decimal_abs, decimal_max

settings = get_settings()


# Metrics
RISK_CHECK_FAILURES = Counter(
    'risk_assessment_failures_total',
    'Number of risk assessment failures by type',
    ['check_type']
)

RISK_LEVELS = Gauge(
    'risk_assessment_levels',
    'Current risk levels by type',
    ['token_address', 'risk_type']
)

RISK_CHECK_DURATION = Histogram(
    'risk_assessment_duration_seconds',
    'Duration of risk assessment checks',
    ['check_type']
)


class RiskType(Enum):
    """Types of risks to assess."""
    MINT_AUTHORITY = auto()
    LIQUIDITY = auto()
    HOLDER_DISTRIBUTION = auto()
    TAX_RATE = auto()
    CONTRACT_SECURITY = auto()
    TRADING_VOLUME = auto()
    PRICE_VOLATILITY = auto()
    SOCIAL_SENTIMENT = auto()


@dataclass
class RiskScore:
    """Container for risk assessment scores."""
    score: float  # 0-100, higher is safer
    details: Dict[str, Any]
    confidence: float  # 0-1, how confident we are in the score
    timestamp: datetime


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""
    token_address: str
    overall_score: float
    risk_scores: Dict[RiskType, RiskScore]
    recommendations: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class RiskAssessmentService:
    """Service for analyzing token contracts and wallet behavior for risks."""

    def __init__(self) -> None:
        """Initialize the risk assessment service with required clients."""
        # Initialize API clients
        self.rug_client = RugcheckClient()
        self.birdeye_client = BirdeyeClient()
        self.dex_client = DexscreenerClient()

        # Risk thresholds from settings
        self.TAX_THRESHOLD = Decimal(settings.max_acceptable_tax)
        self.WHALE_THRESHOLD = Decimal(settings.whale_holder_threshold)
        self.LP_LOCK_MIN_TIME = settings.min_lp_lock_days
        self.MIN_LIQUIDITY = Decimal(settings.min_liquidity_usd)
        self.MAX_PRICE_IMPACT = Decimal(settings.max_price_impact)

        # Cache for risk assessments
        self._cache: Dict[str, RiskAssessment] = {}
        self._cache_ttl = timedelta(minutes=settings.risk_cache_minutes)

    async def is_mint_disabled(self, token_address: str) -> bool:
        """Check if token minting is disabled."""
        try:
            assessment = await self.assess_token(token_address)
            mint_score = assessment.risk_scores.get(RiskType.MINT_AUTHORITY)
            if not mint_score:
                return False
                
            # A score of 100 means minting is disabled
            return mint_score.score >= 95  # Using 95 as threshold to account for analysis confidence
            
        except Exception as e:
            logger.error(f"Error checking mint status for {token_address}: {e}")
            return False  # Assume minting is not disabled if we can't verify

    async def assess_token(self, token_address: str) -> RiskAssessment:
        """Perform complete risk assessment of a token."""
        try:
            # Check cache first
            cached = self._get_cached_assessment(token_address)
            if cached:
                return cached

            # Collect all risk scores concurrently
            tasks = [
                self._check_mint_authority(token_address),
                self._check_liquidity(token_address),
                self._check_holder_distribution(token_address),
                self._check_tax_rates(token_address),
                self._check_contract_security(token_address),
                self._check_trading_metrics(token_address),
                self._check_price_metrics(token_address),
                self._check_social_sentiment(token_address)
            ]

            risk_scores = {}
            warnings = []
            recommendations = []

            # Execute all checks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for risk_type, result in zip(RiskType, results):
                if isinstance(result, Exception):
                    logger.error(f"Error in {risk_type} check: {result}")
                    RISK_CHECK_FAILURES.labels(check_type=risk_type.name).inc()
                    risk_scores[risk_type] = RiskScore(
                        score=0.0,
                        details={"error": str(result)},
                        confidence=0.0,
                        timestamp=datetime.utcnow()
                    )
                else:
                    risk_scores[risk_type] = result

            # Calculate overall score
            weights = {
                RiskType.MINT_AUTHORITY: 0.2,
                RiskType.LIQUIDITY: 0.2,
                RiskType.HOLDER_DISTRIBUTION: 0.15,
                RiskType.TAX_RATE: 0.1,
                RiskType.CONTRACT_SECURITY: 0.15,
                RiskType.TRADING_VOLUME: 0.1,
                RiskType.PRICE_VOLATILITY: 0.05,
                RiskType.SOCIAL_SENTIMENT: 0.05
            }

            overall_score = sum(
                risk_scores[rt].score * risk_scores[rt].confidence * weights[rt]
                for rt in RiskType
            ) / sum(weights.values())

            # Generate assessment
            assessment = RiskAssessment(
                token_address=token_address,
                overall_score=overall_score,
                risk_scores=risk_scores,
                recommendations=self._generate_recommendations(risk_scores),
                warnings=self._generate_warnings(risk_scores),
                metadata={
                    "assessment_time": datetime.utcnow(),
                    "data_confidence": sum(rs.confidence for rs in risk_scores.values()) / len(risk_scores)
                }
            )

            # Update cache and metrics
            self._cache_assessment(token_address, assessment)
            self._update_metrics(token_address, assessment)

            return assessment

        except Exception as e:
            logger.exception(f"Error assessing token {token_address}: {e}")
            raise RiskAssessmentError(f"Risk assessment failed: {str(e)}")

    async def _check_mint_authority(self, token_address: str) -> RiskScore:
        """Check if the token's mint authority is disabled."""
        with RISK_CHECK_DURATION.labels(check_type='mint_authority').time():
            try:
                mint_info = await self.rug_client.get_mint_info(token_address)
                is_disabled = mint_info.get('disabled', False)
                
                score = 100.0 if is_disabled else 0.0
                RISK_LEVELS.labels(
                    token_address=token_address, 
                    risk_type='mint_authority'
                ).set(score)
                
                return RiskScore(
                    score=score,
                    details={
                        "mint_disabled": is_disabled,
                        "mint_authority": mint_info.get('authority'),
                        "last_mint": mint_info.get('last_mint')
                    },
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='mint_authority').inc()
                logger.error(f"Error checking mint authority: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_liquidity(self, token_address: str) -> RiskScore:
        """Check liquidity pool status and risks."""
        with RISK_CHECK_DURATION.labels(check_type='liquidity').time():
            try:
                risks = []
                lp_info = await self.rug_client.get_lp_info(token_address)
                
                # Calculate base score
                score = 0.0
                total_weight = 0.0

                for lp_pair in lp_info.get('pairs', []):
                    liquidity = float(lp_pair.get('liquidity', 0))
                    total_liquidity = float(lp_info.get('total_liquidity', 1))
                    weight = liquidity / total_liquidity
                    
                    lock_days = float(lp_pair.get('lock_time_days', 0))
                    
                    if lock_days >= self.LP_LOCK_MIN_TIME:
                        score += 100.0 * weight
                    elif lock_days > 0:
                        score += (lock_days / self.LP_LOCK_MIN_TIME * 100.0) * weight
                        risks.append('short_lp_lock')
                    else:
                        risks.append('no_lp_lock')
                    
                    total_weight += weight

                final_score = score / total_weight if total_weight > 0 else 0.0
                RISK_LEVELS.labels(token_address=token_address, risk_type='liquidity').set(final_score)
                
                return RiskScore(
                    score=final_score,
                    details={"risks": risks},
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='liquidity').inc()
                logger.error(f"Error checking liquidity: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_holder_distribution(self, token_address: str) -> RiskScore:
        """Analyze wallet distribution and whale concentration."""
        with RISK_CHECK_DURATION.labels(check_type='holder_distribution').time():
            try:
                risks = []
                holder_info = await self.birdeye_client.get_holder_info(token_address)
                
                # Calculate whale concentration
                whale_count = 0
                whale_total = Decimal('0')
                total_supply = Decimal(holder_info.get('total_supply', '0'))
                
                for holder in holder_info.get('holders', []):
                    balance = Decimal(holder.get('balance', '0'))
                    percentage = balance / total_supply if total_supply > 0 else Decimal('0')
                    
                    if percentage >= self.WHALE_THRESHOLD:
                        whale_count += 1
                        whale_total += percentage
                
                if whale_count > 5:
                    risks.append('high_whale_count')
                if whale_total > Decimal('0.50'):
                    risks.append('high_whale_concentration')
                
                # Calculate score (0-100) based on concentration
                # 50% or more in whale wallets = 0 score
                score = float(max(Decimal('0'), Decimal('100') - (whale_total * Decimal('200'))))
                
                RISK_LEVELS.labels(token_address=token_address, risk_type='holder_distribution').set(score)
                return RiskScore(
                    score=score,
                    details={"whale_count": whale_count, "whale_total": float(whale_total)},
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='holder_distribution').inc()
                logger.error(f"Error analyzing holder distribution: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_tax_rates(self, token_address: str) -> RiskScore:
        """Analyze buy/sell tax rates and fee structures."""
        with RISK_CHECK_DURATION.labels(check_type='tax_rate').time():
            try:
                risks = []
                tax_info = await self.rug_client.get_tax_info(token_address)
                
                buy_tax = Decimal(tax_info.get('buy_tax', '0'))
                sell_tax = Decimal(tax_info.get('sell_tax', '0'))
                
                if buy_tax > self.TAX_THRESHOLD:
                    risks.append('high_buy_tax')
                if sell_tax > self.TAX_THRESHOLD:
                    risks.append('high_sell_tax')
                
                # Calculate score (100 = no tax, 0 = max tax of 25% or higher)
                max_tax = max(buy_tax, sell_tax)
                score = float(max(Decimal('0'), Decimal('100') - (max_tax * Decimal('400'))))  # 25% tax = 0 score
                
                RISK_LEVELS.labels(token_address=token_address, risk_type='tax_rate').set(score)
                return RiskScore(
                    score=score,
                    details={"buy_tax": float(buy_tax), "sell_tax": float(sell_tax)},
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='tax_rate').inc()
                logger.error(f"Error analyzing tax rates: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_contract_security(self, token_address: str) -> RiskScore:
        """Get contract audit status and score."""
        with RISK_CHECK_DURATION.labels(check_type='contract_security').time():
            try:
                audit_info = await self.rug_client.get_audit_info(token_address)
                
                # Base score on audit status and age
                score = 0.0
                if audit_info.get('has_audit', False):
                    score = 80.0  # Base score for having an audit
                    
                    # Add points for audit quality
                    if audit_info.get('major_issues', 0) == 0:
                        score += 20.0
                    elif audit_info.get('critical_issues', 0) == 0:
                        score += 10.0
                
                RISK_LEVELS.labels(token_address=token_address, risk_type='contract_security').set(score)
                return RiskScore(
                    score=score,
                    details={
                        "has_audit": audit_info.get('has_audit'),
                        "audit_score": score,
                        "major_issues": audit_info.get('major_issues'),
                        "critical_issues": audit_info.get('critical_issues')
                    },
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='contract_security').inc()
                logger.error(f"Error getting contract security info: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_trading_metrics(self, token_address: str) -> RiskScore:
        """Check token trading metrics."""
        with RISK_CHECK_DURATION.labels(check_type='trading_metrics').time():
            try:
                pairs = await self.dex_client.get_token_pairs(token_address)
                if not pairs:
                    RISK_CHECK_FAILURES.labels(check_type='trading_metrics').inc()
                    return RiskScore(
                        score=0.0,
                        details={"error": "No trading pairs found"},
                        confidence=0.0,
                        timestamp=datetime.utcnow()
                    )
                
                # Use the pair with highest liquidity for metrics
                best_pair = max(pairs, key=lambda p: p.liquidity_usd)
                
                # Calculate score based on volume and volatility
                volume_score = 0
                if best_pair.volume_24h > 0 and best_pair.liquidity_usd > 0:
                    # Volume score from 0-100 based on volume vs liquidity ratio
                    volume_ratio = best_pair.volume_24h / best_pair.liquidity_usd
                    volume_score = min(int(volume_ratio * 100), 100)  # Cap at 100
                
                # Calculate liquidity score
                liquidity_score = min(int((best_pair.liquidity_usd / 10000) * 100), 100)
                
                # Calculate price volatility score (inverse of absolute price change)
                volatility_score = max(0, 100 - abs(best_pair.price_change_24h))
                
                # Weighted average of scores
                total_score = (volume_score * 0.4 + liquidity_score * 0.4 + volatility_score * 0.2)
                
                details = {
                    "volume_24h": best_pair.volume_24h,
                    "liquidity_usd": best_pair.liquidity_usd,
                    "price_change_24h": best_pair.price_change_24h,
                    "volume_score": volume_score,
                    "liquidity_score": liquidity_score,
                    "volatility_score": volatility_score
                }
                
                return self._create_risk_score(total_score, details, 0.9)

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='trading_metrics').inc()
                logger.error(f"Error analyzing trading metrics: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    async def _check_price_metrics(self, token_address: str) -> RiskScore:
        """Check token price metrics."""
        try:
            pairs = await self.dex_client.get_token_pairs(token_address)
            if not pairs:
                return RiskScore(
                    score=0.0,
                    details={"error": "No price metrics available"},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )
            
            # Use the pair with highest liquidity
            best_pair = max(pairs, key=lambda p: p.liquidity_usd)
            price_change = Decimal(str(best_pair.price_change_24h))
            liquidity = Decimal(str(best_pair.liquidity_usd))
            
            # Price stability score (0-100)
            if decimal_abs(price_change) <= 5:
                stability_score = 100
            elif decimal_abs(price_change) <= 10:
                stability_score = 75
            elif decimal_abs(price_change) <= 20:
                stability_score = 50
            elif decimal_abs(price_change) <= 30:
                stability_score = 25
            else:
                stability_score = 0
                
            # Liquidity score (0-100)
            if liquidity >= self.MIN_LIQUIDITY:
                liquidity_score = 100
            else:
                liquidity_score = min(int((liquidity / self.MIN_LIQUIDITY) * 100), 99)
                
            # Volume health score (0-100)
            volume_score = 0
            if best_pair.volume_24h > 0 and liquidity > 0:
                # Volume score based on volume vs liquidity ratio
                volume_ratio = float(best_pair.volume_24h) / float(liquidity)
                volume_score = min(int(volume_ratio * 100), 100)
                
            # Calculate final score with weights
            final_score = (stability_score * 0.4 + 
                         liquidity_score * 0.4 + 
                         volume_score * 0.2)
                         
            return RiskScore(
                score=final_score,
                details={
                    "price_change_24h": float(price_change),
                    "liquidity_usd": float(liquidity),
                    "volume_24h": best_pair.volume_24h,
                    "stability_score": stability_score,
                    "liquidity_score": liquidity_score,
                    "volume_score": volume_score,
                    "dex": best_pair.dex,
                    "pair": best_pair.pair_address
                },
                confidence=0.9 if liquidity >= self.MIN_LIQUIDITY else 0.7,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error checking price metrics: {e}")
            return RiskScore(
                score=0.0,
                details={"error": str(e)},
                confidence=0.0,
                timestamp=datetime.utcnow()
            )

    async def _check_social_sentiment(self, token_address: str) -> RiskScore:
        """Analyze social media sentiment and mentions."""
        with RISK_CHECK_DURATION.labels(check_type='social_sentiment').time():
            try:
                # For social sentiment, we can use a simple metric like the number of positive vs negative mentions
                sentiment_data = await self.birdeye_client.get_social_sentiment(token_address)
                
                positive_mentions = sentiment_data.get('positive_mentions', 0)
                negative_mentions = sentiment_data.get('negative_mentions', 0)
                
                # Calculate score based on sentiment ratio
                if positive_mentions + negative_mentions > 0:
                    sentiment_ratio = positive_mentions / (positive_mentions + negative_mentions)
                    score = sentiment_ratio * 100
                else:
                    score = 50.0  # Neutral score if no mentions
                
                RISK_LEVELS.labels(token_address=token_address, risk_type='social_sentiment').set(score)
                return RiskScore(
                    score=score,
                    details={
                        "positive_mentions": positive_mentions,
                        "negative_mentions": negative_mentions
                    },
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                RISK_CHECK_FAILURES.labels(check_type='social_sentiment').inc()
                logger.error(f"Error analyzing social sentiment: {e}")
                return RiskScore(
                    score=0.0,
                    details={"error": str(e)},
                    confidence=0.0,
                    timestamp=datetime.utcnow()
                )

    def _get_cached_assessment(self, token_address: str) -> Optional[RiskAssessment]:
        """Get cached risk assessment if valid."""
        try:
            assessment = self._cache.get(token_address)
            if assessment is None:
                return None
                
            assessment_time = assessment.metadata.get('assessment_time')
            if not isinstance(assessment_time, datetime):
                return None
                
            if (datetime.utcnow() - assessment_time) < self._cache_ttl:
                return assessment
                
            return None
            
        except Exception as e:
            logger.error(f"Error accessing risk assessment cache: {e}")
            return None
            
    def _cache_assessment(self, token_address: str, assessment: RiskAssessment) -> None:
        """Cache risk assessment result."""
        try:
            # Clean old cache entries if needed
            if len(self._cache) >= settings.max_cache_size:
                # Remove oldest entries
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].metadata.get('assessment_time', datetime.min)
                )
                for old_key, _ in sorted_items[:10]:  # Remove oldest 10
                    self._cache.pop(old_key, None)
                    
            self._cache[token_address] = assessment
            
        except Exception as e:
            logger.error(f"Error caching risk assessment: {e}")
            
    def _update_metrics(self, token_address: str, assessment: RiskAssessment) -> None:
        """Update Prometheus metrics from risk assessment."""
        try:
            for risk_type, risk_score in assessment.risk_scores.items():
                RISK_LEVELS.labels(
                    token_address=token_address,
                    risk_type=risk_type.name.lower()
                ).set(risk_score.score)
                
        except Exception as e:
            logger.error(f"Error updating risk metrics: {e}")
            
    @classmethod
    def _generate_warnings(cls, risk_scores: Dict[RiskType, RiskScore]) -> List[str]:
        """Generate warning messages from risk scores."""
        warnings = []
        
        # Check mint authority
        if (RiskType.MINT_AUTHORITY in risk_scores and 
            risk_scores[RiskType.MINT_AUTHORITY].score < 50):
            warnings.append("⚠️ Mint authority is not disabled")
            
        # Check liquidity
        if (RiskType.LIQUIDITY in risk_scores and 
            risk_scores[RiskType.LIQUIDITY].score < 50):
            warnings.append("⚠️ Low liquidity - high risk of price manipulation")
            
        # Check holder distribution
        if (RiskType.HOLDER_DISTRIBUTION in risk_scores and 
            risk_scores[RiskType.HOLDER_DISTRIBUTION].score < 50):
            warnings.append("⚠️ Concentrated holder distribution - risk of dumps")
            
        # Check tax rates
        if (RiskType.TAX_RATE in risk_scores and 
            risk_scores[RiskType.TAX_RATE].score < 50):
            warnings.append("⚠️ High tax rates may impact trading")
            
        # Check contract security
        if (RiskType.CONTRACT_SECURITY in risk_scores and 
            risk_scores[RiskType.CONTRACT_SECURITY].score < 50):
            warnings.append("⚠️ Contract security issues detected")
            
        return warnings
        
    @classmethod
    def _generate_recommendations(cls, risk_scores: Dict[RiskType, RiskScore]) -> List[str]:
        """Generate recommendation messages from risk scores."""
        recommendations = []
        
        # Add recommendations based on scores
        for risk_type, risk_score in risk_scores.items():
            if risk_score.score < 50:
                if risk_type == RiskType.MINT_AUTHORITY:
                    recommendations.append("🔒 Wait for mint authority to be disabled")
                elif risk_type == RiskType.LIQUIDITY:
                    recommendations.append("💧 Wait for more liquidity to be added")
                elif risk_type == RiskType.HOLDER_DISTRIBUTION:
                    recommendations.append("👥 Monitor whale wallet movements")
                elif risk_type == RiskType.TAX_RATE:
                    recommendations.append("💰 Consider tax impact on trades")
                elif risk_type == RiskType.CONTRACT_SECURITY:
                    recommendations.append("🔍 Review contract security audit")
                    
        return recommendations
    
    def _create_risk_score(self, score: float, details: Dict[str, Any], confidence: float) -> RiskScore:
        """Create a RiskScore object."""
        return RiskScore(
            score=score,
            details=details,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
