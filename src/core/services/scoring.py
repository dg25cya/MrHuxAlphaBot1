"""Token scoring service."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.token import Token
from src.models.token_score import TokenScore
from src.models.token_metrics import TokenMetrics
from src.models.mention import TokenMention
from src.models.group import MonitoredGroup
from src.utils import get_utc_now
from src.utils.type_conversion import safe_float, safe_int


def calculate_liquidity_scores(metrics: TokenMetrics) -> Dict[str, float]:
    """Calculate liquidity-related scores for token metrics."""
    try:
        # Convert Decimal/Numeric values to float using safe conversion
        liquidity_usd = safe_float(metrics.liquidity)
        market_cap = safe_float(metrics.market_cap)
        volume_24h = safe_float(metrics.volume_24h)
        
        # Score liquidity (0-100)
        liquidity_score = min(100, (100 * liquidity_usd) / 1_000_000) if liquidity_usd else 0
        
        # Score market cap (0-100)
        market_cap_score = min(100, (100 * market_cap) / 10_000_000) if market_cap else 0
        if market_cap_score > 100_000_000:  # Penalize high caps
            market_cap_score *= 0.8
            
        # Score volume (0-100)
        volume_score = min(100, (100 * volume_24h) / 100_000) if volume_24h else 0
        
        # Composite score with equal weights
        composite = (liquidity_score + market_cap_score + volume_score) / 3
        
        return {
            "liquidity_score": liquidity_score,
            "market_cap_score": market_cap_score,
            "volume_score": volume_score,
            "composite": composite
        }
    except Exception as e:
        logger.error(f"Error calculating liquidity scores: {e}")
        return {
            "liquidity_score": 0,
            "market_cap_score": 0,
            "volume_score": 0,
            "composite": 0
        }


def calculate_safety_scores(metrics: TokenMetrics) -> Dict[str, float]:
    """Calculate safety-related scores for token metrics."""
    try:
        # Convert SQLAlchemy Column objects to actual values using safe conversion
        buy_tax = safe_float(metrics.buy_tax)
        sell_tax = safe_float(metrics.sell_tax)
        
        # Base safety metrics
        base_score = 100
        
        # Tax deductions
        tax_deduction = 0
        if buy_tax:
            tax_deduction += buy_tax * 5  # -5 points per 1% tax
        if sell_tax:
            tax_deduction += sell_tax * 5
            
        # Additional safety factors from raw_metrics
        raw = metrics.raw_metrics or {}
        contract_verified = raw.get("contract_verified", False)
        owner_renounced = raw.get("owner_renounced", False)
        liquidity_locked = raw.get("liquidity_locked", False)
        is_honeypot = raw.get("is_honeypot", True)
        
        # Calculate component scores
        contract_score = 100 if contract_verified else 0
        ownership_score = 100 if owner_renounced else 0
        liquidity_lock_score = 100 if liquidity_locked else 0
        honeypot_score = 0 if is_honeypot else 100
        
        # Calculate final safety score
        safety_score = base_score - tax_deduction
        safety_score = min(max(safety_score, 0), 100)  # Clamp between 0-100
        
        # Composite using weighted average
        weights = {
            "contract": 0.3,
            "ownership": 0.3,
            "liquidity": 0.2,
            "honeypot": 0.2
        }
        
        composite = (
            contract_score * weights["contract"] +
            ownership_score * weights["ownership"] +
            liquidity_lock_score * weights["liquidity"] +
            honeypot_score * weights["honeypot"]
        )
        
        return {
            "contract_safety_score": contract_score,
            "ownership_score": ownership_score,
            "liquidity_lock_score": liquidity_lock_score,
            "honeypot_risk_score": honeypot_score,
            "composite": composite
        }
    except Exception as e:
        logger.error(f"Error calculating safety scores: {e}")
        return {
            "contract_safety_score": 0,
            "ownership_score": 0,
            "liquidity_lock_score": 0,
            "honeypot_risk_score": 0,
            "composite": 0
        }


def calculate_social_scores(token_id: int, db: Session, timeframe: timedelta = timedelta(hours=24)) -> Dict[str, float]:
    """Calculate social metric scores for a token."""
    try:
        since = get_utc_now() - timeframe
        
        # Get mention count in timeframe
        mention_count = db.query(func.count(TokenMention.id)).filter(
            TokenMention.token_id == token_id,
            TokenMention.mentioned_at >= since
        ).scalar() or 0
        
        # Calculate mention frequency score (0-100)
        mention_score = min(100, mention_count * 10)
        
        # Calculate average source reliability
        avg_reliability = db.query(
            func.avg(MonitoredGroup.weight)
        ).join(
            TokenMention, TokenMention.group_id == MonitoredGroup.id
        ).filter(
            TokenMention.token_id == token_id,
            TokenMention.mentioned_at >= since
        ).scalar() or 0
        
        # Scale reliability to 0-100
        reliability_score = float(avg_reliability) * 100
        
        # Get average sentiment
        avg_sentiment = db.query(
            func.avg(TokenMention.sentiment)
        ).filter(
            TokenMention.token_id == token_id,
            TokenMention.mentioned_at >= since
        ).scalar() or 0
        
        # Scale sentiment from [-1,1] to [0,100]
        sentiment_score = (float(avg_sentiment) + 1) * 50
        
        # Composite using weighted average
        weights = {
            "mentions": 0.4,
            "reliability": 0.3,
            "sentiment": 0.3
        }
        
        composite = (
            mention_score * weights["mentions"] +
            reliability_score * weights["reliability"] +
            sentiment_score * weights["sentiment"]
        )
        
        return {
            "mention_frequency_score": mention_score,
            "source_reliability_score": reliability_score,
            "sentiment_score": sentiment_score,
            "composite": composite
        }
    except Exception as e:
        logger.error(f"Error calculating social scores: {e}")
        return {
            "mention_frequency_score": 0,
            "source_reliability_score": 0,
            "sentiment_score": 0,
            "composite": 0
        }


async def calculate_token_score(token: Token, metrics: TokenMetrics, db: Session) -> Optional[TokenScore]:
    """Calculate a fresh score for a token."""
    try:
        # Calculate component scores
        liquidity_scores = calculate_liquidity_scores(metrics)
        safety_scores = calculate_safety_scores(metrics)
        social_scores = calculate_social_scores(safe_int(token.id), db)
        
        # Calculate final weighted score
        weights = {
            "liquidity": 0.3,
            "safety": 0.4,
            "social": 0.3
        }
        
        total_score = (
            liquidity_scores["composite"] * weights["liquidity"] +
            safety_scores["composite"] * weights["safety"] +
            social_scores["composite"] * weights["social"]
        )
        
        # Create and save score
        score = TokenScore(
            token_id=token.id,
            # Liquidity metrics
            liquidity_score=liquidity_scores["liquidity_score"],
            market_cap_score=liquidity_scores["market_cap_score"],
            volume_score=liquidity_scores["volume_score"],
            liquidity_composite=liquidity_scores["composite"],
            
            # Safety metrics
            contract_safety_score=safety_scores["contract_safety_score"],
            ownership_score=safety_scores["ownership_score"],
            liquidity_lock_score=safety_scores["liquidity_lock_score"],
            honeypot_risk_score=safety_scores["honeypot_risk_score"],
            safety_composite=safety_scores["composite"],
            
            # Social metrics
            mention_frequency_score=social_scores["mention_frequency_score"],
            source_reliability_score=social_scores["source_reliability_score"],
            sentiment_score=social_scores["sentiment_score"],
            social_composite=social_scores["composite"],
            
            # Final score
            total_score=total_score,
            
            # Store raw metrics for reference
            raw_metrics=metrics.raw_metrics
        )
        
        db.add(score)
        db.commit()
        
        return score
        
    except Exception as e:
        logger.exception(f"Error calculating token score: {e}")
        return None


class ScoringService:
    """Service for calculating token scores."""
    
    def __init__(self, db: Session) -> None:
        """Initialize scoring service."""
        self.db = db
    
    def calculate_liquidity_scores(self, metrics: TokenMetrics) -> Dict[str, float]:
        """Calculate liquidity-related scores for token metrics."""
        return calculate_liquidity_scores(metrics)
    
    def calculate_safety_scores(self, metrics: TokenMetrics) -> Dict[str, float]:
        """Calculate safety-related scores for token metrics."""
        return calculate_safety_scores(metrics)
    
    def calculate_social_scores(self, token_id: int, timeframe: timedelta = timedelta(hours=24)) -> Dict[str, float]:
        """Calculate social metric scores for a token."""
        return calculate_social_scores(token_id, self.db, timeframe)
    
    async def calculate_token_score(self, token: Token, metrics: TokenMetrics) -> Optional[TokenScore]:
        """Calculate a fresh score for a token."""
        return await calculate_token_score(token, metrics, self.db)
