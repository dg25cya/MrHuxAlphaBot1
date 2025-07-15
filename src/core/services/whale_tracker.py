"""Whale wallet tracking and analysis service."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal

from loguru import logger
from prometheus_client import Counter, Histogram
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...models.token import Token
from ...models.alerts import Alert
from ...api.clients.birdeye import BirdeyeClient
from ...config.settings import get_settings
from ...database import get_db

settings = get_settings()

# Metrics
WHALE_TRANSFERS = Counter(
    'whale_transfers_total',
    'Number of whale transfers detected',
    ['token', 'type']
)

WHALE_HOLDERS = Counter(
    'whale_holders_total',
    'Number of whale holders tracked',
    ['token']
)

HOLDER_CONCENTRATION = Histogram(
    'holder_concentration',
    'Token holder concentration (top 10 holders percentage)',
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

class WhaleTracker:
    """Service for tracking and analyzing whale wallet activity."""
    
    def __init__(self) -> None:
        """Initialize the whale tracker service."""
        self.birdeye = BirdeyeClient()
        self.running = False
        self.whale_thresholds = {
            'transfer_amount': Decimal('10000'),  # $10k min for whale transfer
            'holder_percentage': Decimal('1'),    # 1% of supply for whale holder
            'max_concentration': Decimal('60'),   # 60% max for top 10 holders
        }
        self._task = None
        
    async def start(self):
        """Start the whale tracking service."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._tracking_loop())
        logger.info("Whale tracking service started")
        
    async def stop(self):
        """Stop the whale tracking service."""
        if not self.running:
            return
            
        self.running = False
        if self._task:
            await self._task
        logger.info("Whale tracking service stopped")
        
    async def _tracking_loop(self):
        """Main tracking loop."""
        while self.running:
            try:
                # Get active tokens to monitor
                async with get_db() as db:
                    tokens = await self._get_active_tokens(db)
                    
                # Process each token
                for token in tokens:
                    await self._process_token(token)
                    
                # Sleep between cycles
                await asyncio.sleep(60)  # Check every minute
                    
            except Exception as e:
                logger.error(f"Error in whale tracking loop: {e}")
                await asyncio.sleep(5)
                
    async def _get_active_tokens(self, db: Session) -> List[Token]:
        """Get list of active tokens to monitor."""
        query = text("""
            SELECT t.* FROM tokens t
            JOIN token_metrics tm ON t.id = tm.token_id
            WHERE tm.timestamp >= NOW() - INTERVAL '24 hours'
            AND tm.liquidity > :min_liquidity
            AND NOT t.is_blacklisted
            """)
        
        result = await db.execute(
            query,
            {'min_liquidity': float(self.whale_thresholds['transfer_amount'])}
        )
        return result.fetchall()
        
    async def _process_token(self, token: Token):
        """Process and analyze whale activity for a token."""
        try:
            # Get holders data
            holders = await self.birdeye.get_token_holders(token.address)
            
            # Calculate supply concentration
            total_supply = sum(h.balance for h in holders)
            if total_supply == 0:
                return
            
            # Sort holders by balance
            holders.sort(key=lambda h: h.balance, reverse=True)
            
            # Calculate top holder concentration
            top_holders = holders[:10]
            top_balance = sum(h.balance for h in top_holders)
            concentration = (top_balance / total_supply) * 100
            
            # Track metrics
            HOLDER_CONCENTRATION.observe(concentration)
            
            # Check for dangerous concentration
            if concentration > self.whale_thresholds['max_concentration']:
                await self._create_concentration_alert(token, concentration)
            
            # Track whale moves
            for holder in holders:
                percentage = (holder.balance / total_supply) * 100
                if percentage >= self.whale_thresholds['holder_percentage']:
                    WHALE_HOLDERS.labels(token=token.address).inc()
                    await self._monitor_whale_wallet(token, holder.address, percentage)
                    
        except Exception as e:
            logger.error(f"Error processing token {token.address}: {e}")
            
    async def _monitor_whale_wallet(self, token: Token, wallet: str, percentage: float):
        """Monitor a whale wallet for significant transfers."""
        try:
            # Get recent transfers
            transfers = await self.birdeye.get_wallet_transfers(
                wallet,
                token_address=token.address,
                limit=10
            )
            
            for transfer in transfers:
                if transfer.value_usd >= self.whale_thresholds['transfer_amount']:
                    transfer_type = 'buy' if transfer.is_buy else 'sell'
                    WHALE_TRANSFERS.labels(
                        token=token.address,
                        type=transfer_type
                    ).inc()
                    
                    await self._create_whale_alert(
                        token,
                        wallet,
                        transfer,
                        percentage
                    )
                    
        except Exception as e:
            logger.error(f"Error monitoring whale wallet {wallet}: {e}")
            
    async def _create_whale_alert(
        self,
        token: Token,
        wallet: str,
        transfer: Any,
        holder_percentage: float
    ):
        """Create an alert for significant whale activity."""
        async with get_db() as db:
            alert = Alert(
                token_id=token.id,
                alert_type='whale_transfer',
                verdict='WARNING' if transfer.is_sell else 'INFO',
                metrics_snapshot={
                    'wallet': wallet,
                    'amount_usd': str(transfer.value_usd),
                    'holder_percentage': holder_percentage,
                    'is_sell': transfer.is_sell,
                    'timestamp': transfer.timestamp.isoformat()
                }
            )
            db.add(alert)
            await db.commit()
            
    async def _create_concentration_alert(
        self,
        token: Token,
        concentration: float
    ):
        """Create an alert for dangerous holder concentration."""
        async with get_db() as db:
            alert = Alert(
                token_id=token.id,
                alert_type='high_concentration',
                verdict='WARNING',
                metrics_snapshot={
                    'concentration': concentration,
                    'threshold': float(self.whale_thresholds['max_concentration']),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            db.add(alert)
            await db.commit()
