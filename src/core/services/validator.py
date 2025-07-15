"""Token validation service."""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.orm import Session
from telethon import TelegramClient

from src.api.clients.dexscreener import DexscreenerClient
from src.schemas.token_data import TokenMarketData
from src.api.clients.rugcheck import RugcheckClient
from src.schemas.token_safety import TokenSafetyData
from src.api.clients.pumpfun import PumpfunClient, TokenLaunchData
from src.api.clients.bonkfun import BonkfunClient, BonkLaunchData
from src.core.services.scoring import ScoringService
from src.core.services.alert_service import check_token_alerts
from src.models.token import Token
from src.models.token_metrics import TokenMetrics
from src.models.token_score import TokenScore
from src.utils import get_utc_now


@dataclass
class TokenValidationResult:
    """Container for token validation results."""
    address: str
    market_data: Optional[TokenMarketData] = None
    safety_data: Optional[TokenSafetyData] = None
    launch_data: Optional[TokenLaunchData] = None
    bonk_data: Optional[BonkLaunchData] = None
    score: Optional[TokenScore] = None
    validation_time: datetime = get_utc_now()
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if token has passed basic validation."""
        if not self.market_data or not self.safety_data:
            return False
            
        # Must have some liquidity
        if self.market_data.liquidity_usd < 1000:  # $1k minimum
            return False
            
        # Must not be flagged as honeypot
        if self.safety_data.is_honeypot:
            return False
            
        # Maximum tax threshold
        if self.safety_data.buy_tax >= 15 or self.safety_data.sell_tax >= 15:
            return False
            
        return True
    
    @property
    def verdict(self) -> str:
        """Get validation verdict."""
        if self.error_message:
            return "ERROR"
        return "VALID" if self.is_valid else "INVALID"
    
    @property
    def is_honeypot(self) -> bool:
        """Check if token is flagged as honeypot."""
        return bool(self.safety_data and self.safety_data.is_honeypot)
    
    @property
    def high_tax(self) -> bool:
        """Check if token has high buy/sell tax."""
        return bool(self.safety_data and (self.safety_data.buy_tax >= 15 or self.safety_data.sell_tax >= 15))
    
    @property
    def insufficient_liquidity(self) -> bool:
        """Check if token has insufficient liquidity."""
        return bool(self.market_data and self.market_data.liquidity_usd < 1000)
    
    @property
    def risk_level(self) -> Optional[str]:
        """Get token risk level."""
        return self.safety_data.risk_level if self.safety_data else None
    
    def to_dict(self) -> Dict:
        """Convert validation result to dictionary."""
        base_dict = {
            "address": self.address,
            "price_usd": self.market_data.price_usd if self.market_data else None,
            "liquidity_usd": self.market_data.liquidity_usd if self.market_data else None,
            "volume_24h": self.market_data.volume_24h if self.market_data else None,
            "price_change_24h": self.market_data.price_change_24h if self.market_data else None,
            "holders_count": self.safety_data.holders_count if self.safety_data else None,
            "is_mint_disabled": self.safety_data.is_mint_disabled if self.safety_data else None,
            "lp_locked": self.safety_data.lp_locked if self.safety_data else None,
            "risk_level": self.safety_data.risk_level if self.safety_data else None,
            "buy_tax": self.safety_data.buy_tax if self.safety_data else None,
            "sell_tax": self.safety_data.sell_tax if self.safety_data else None,
            "launch_platform": "pump.fun" if self.launch_data else ("bonk.fun" if self.bonk_data else None),
            "validation_time": self.validation_time.isoformat()
        }
        
        if self.score:
            base_dict.update({
                "total_score": self.score.total_score,
                "liquidity_score": self.score.liquidity_composite,
                "safety_score": self.score.safety_composite,
                "social_score": self.score.social_composite
            })
            
        return base_dict


async def validate_token(
    token_address: str,
    db: Optional[Session] = None,
    client: Optional[TelegramClient] = None
) -> TokenValidationResult:
    """
    Validate a token by checking liquidity, safety, and other metrics.
    
    Args:
        token_address: Token address to validate
        db: Optional database session
        client: Optional Telegram client for sending alerts
        
    Returns:
        TokenValidationResult containing validation data
    """
    result = TokenValidationResult(address=token_address)
    
    try:        # Get market data
        dexscreener = DexscreenerClient()
        result.market_data = await dexscreener.get_token_pairs(token_address)
          # Get safety data
        rugcheck = RugcheckClient()
        result.safety_data = await rugcheck.check_token(token_address)
          # Try to get listing data from pump.fun
        pump = PumpfunClient()
        result.launch_data = await pump.get_token_info(token_address)
        
        # If not on pump.fun, try bonk.fun
        if not result.launch_data:
            bonk = BonkfunClient()
            result.bonk_data = await bonk.get_token_info(token_address)
          # Get or create token record if we have a DB
        token = None
        if db and result.market_data and result.safety_data:
            # Try to find existing token
            token = db.query(Token).filter(
                Token.address == token_address
            ).first()
            
            if not token:
                # Create new token record
                token = Token(
                    address=token_address,
                    first_seen_at=get_utc_now(),
                    last_updated_at=get_utc_now())
                db.add(token)
                db.flush()  # Get token.id
            else:
                token.last_updated_at = get_utc_now()
                
            # Create metrics record
            metrics = TokenMetrics(
                token_id=token.id,
                price=result.market_data.price_usd,
                market_cap=result.market_data.market_cap,
                volume_24h=result.market_data.volume_24h,
                liquidity_usd=result.market_data.liquidity_usd,
                holder_count=result.safety_data.holders_count,
                buy_tax=result.safety_data.buy_tax,
                sell_tax=result.safety_data.sell_tax,
                raw_metrics={
                    "contract_verified": result.safety_data.is_verified,
                    "owner_renounced": not result.safety_data.mint_authority,
                    "liquidity_locked": result.safety_data.lp_locked,
                    "is_honeypot": result.safety_data.is_honeypot,
                    "risk_level": result.safety_data.risk_level,
                    "risk_factors": result.safety_data.risk_factors,
                    "pair_address": result.market_data.pair_address,
                    "has_launch_data": bool(result.launch_data or result.bonk_data)
                },
                created_at=get_utc_now()
            )
            db.add(metrics)            # Store metrics
            metrics = TokenMetrics(
                token_id=token.id,
                price=result.market_data.price_usd,
                market_cap=result.market_data.market_cap,
                volume_24h=result.market_data.volume_24h,
                liquidity_usd=result.market_data.liquidity_usd,
                holder_count=result.safety_data.holders_count,
                buy_tax=result.safety_data.buy_tax,
                sell_tax=result.safety_data.sell_tax,
                created_at=get_utc_now()
            )
            db.add(metrics)

            # Calculate score
            scoring = ScoringService(db)
            result.score = await scoring.calculate_token_score(token, metrics)
              # Store score
            db_score = TokenScore(
                token_id=token.id,
                liquidity_score=result.score.liquidity_score,
                safety_score=result.score.safety_score,
                social_score=result.score.social_score,
                total_score=result.score.total_score,
                created_at=get_utc_now()
            )
            db.add(db_score)
              # Generate alerts if we have both DB and client
            if client:
                await check_token_alerts(token, metrics, db_score, db, client)
            
            db.commit()
                
    except Exception as e:
        logger.exception(f"Error validating token {token_address}: {e}")
        result.error_message = str(e)
    
    return result


class TokenValidator:
    """Service for validating tokens using multiple data sources."""
    
    def __init__(self, db: Session) -> None:
        """Initialize API clients and services."""
        self.db = db
        self.dexscreener = DexscreenerClient()
        self.rugcheck = RugcheckClient()
        self.pumpfun = PumpfunClient()
        self.bonkfun = BonkfunClient()
        self.scoring = ScoringService(db)

    async def validate_token(self, address: str, client: Optional[TelegramClient] = None) -> TokenValidationResult:
        """
        Validate a token by checking liquidity, safety, and other metrics.
        
        Args:
            address: Token address to validate
            client: Optional Telegram client for sending alerts
            
        Returns:
            TokenValidationResult containing validation data
        """
        return await validate_token(address, self.db, client)

    async def close(self):
        """Close all API clients."""
        await asyncio.gather(
            self.dexscreener.close(),
            self.rugcheck.close(),
            self.pumpfun.close(),
            self.bonkfun.close()
        )
