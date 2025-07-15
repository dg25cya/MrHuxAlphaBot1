"""
Service for tracking large wallet movements and whale activity.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging

from src.api.clients.birdeye import BirdeyeClient
from src.models.token import Token
from src.core.monitoring import WhaleMetrics
from src.utils.solana_utils import validate_solana_address
from src.utils.redis_cache import RedisCache

logger = logging.getLogger(__name__)

class WalletTracker:
    def __init__(
        self,
        birdeye_client: BirdeyeClient,
        redis_cache: RedisCache,
        whale_threshold: float = 10000,  # $10k USD minimum for whale tx
        tracking_window: int = 24,  # Hours to track
    ):
        self.birdeye_client = birdeye_client
        self.redis_cache = redis_cache
        self.whale_threshold = whale_threshold
        self.tracking_window = tracking_window
        self.metrics = WhaleMetrics()
        self._whale_wallets: Set[str] = set()

    async def track_token_movements(self, token: Token) -> Dict[str, any]:
        """
        Track large movements for a given token.
        Returns whale activity metrics.
        """
        if not validate_solana_address(token.address):
            logger.error(f"Invalid token address: {token.address}")
            return {}

        # Get recent transfers
        transfers = await self._get_token_transfers(token.address)
        if not transfers:
            return {}

        # Analyze transfers
        whale_data = await self._analyze_transfers(token.address, transfers)
        
        # Cache whale wallets
        await self._update_whale_wallets(whale_data["whale_wallets"])
        
        return whale_data

    async def get_whale_wallets(self) -> Set[str]:
        """Get the set of known whale wallets."""
        return self._whale_wallets

    async def _get_token_transfers(self, token_address: str) -> List[Dict]:
        """Get recent token transfers from Birdeye."""
        try:
            # Get transfers for last tracking_window hours
            since = datetime.utcnow() - timedelta(hours=self.tracking_window)
            
            transfers = await self.birdeye_client.get_token_transfers(
                token_address,
                since=since
            )
            
            if transfers:
                self.metrics.record_transfer_count(token_address, len(transfers))
            
            return transfers

        except Exception as e:
            logger.error(f"Error getting token transfers: {e}")
            return []

    async def _analyze_transfers(
        self,
        token_address: str,
        transfers: List[Dict]
    ) -> Dict[str, any]:
        """Analyze transfers to detect whale activity."""
        whale_wallets = set()
        total_volume = 0
        buy_pressure = 0
        sell_pressure = 0

        for transfer in transfers:
            amount_usd = transfer.get("amount_usd", 0)
            if amount_usd >= self.whale_threshold:
                whale_wallets.add(transfer["from_address"])
                whale_wallets.add(transfer["to_address"])
                
                total_volume += amount_usd
                if transfer.get("is_buy", False):
                    buy_pressure += amount_usd
                else:
                    sell_pressure += amount_usd

        # Calculate metrics
        net_flow = buy_pressure - sell_pressure
        pressure_ratio = (buy_pressure / sell_pressure) if sell_pressure > 0 else float('inf')

        self.metrics.record_whale_metrics(
            token_address,
            len(whale_wallets),
            total_volume,
            pressure_ratio
        )

        return {
            "whale_wallets": whale_wallets,
            "total_volume_usd": total_volume,
            "buy_pressure_usd": buy_pressure,
            "sell_pressure_usd": sell_pressure,
            "net_flow_usd": net_flow,
            "pressure_ratio": pressure_ratio
        }

    async def _update_whale_wallets(self, new_whales: Set[str]):
        """Update the cache of known whale wallets."""
        self._whale_wallets.update(new_whales)
        
        # Store in Redis for persistence
        try:
            await self.redis_cache.set(
                "whale_wallets",
                list(self._whale_wallets),
                expire_seconds=self.tracking_window * 3600
            )
        except Exception as e:
            logger.error(f"Error caching whale wallets: {e}")

    async def get_wallet_tokens(self, wallet_address: str) -> List[Dict]:
        """Get all tokens held by a wallet."""
        try:
            if not validate_solana_address(wallet_address):
                logger.error(f"Invalid wallet address: {wallet_address}")
                return []

            holdings = await self.birdeye_client.get_wallet_holdings(wallet_address)
            return [
                {
                    "token_address": h["token_address"],
                    "balance": h["balance"],
                    "value_usd": h["value_usd"]
                }
                for h in holdings if h.get("value_usd", 0) >= self.whale_threshold
            ]

        except Exception as e:
            logger.error(f"Error getting wallet tokens: {e}")
            return []
