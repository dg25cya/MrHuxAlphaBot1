"""
The security analyzer service combines data from multiple sources to analyze token security.
"""
import asyncio
from typing import Dict, List, Optional, Tuple
import logging

from src.api.clients.rugcheck import RugcheckClient
from src.api.clients.birdeye import BirdeyeClient
from src.models.token import Token
from src.core.monitoring import SecurityMetrics
from src.utils.solana_utils import validate_solana_address

logger = logging.getLogger(__name__)

class SecurityAnalyzer:
    def __init__(
        self,
        rugcheck_client: RugcheckClient,
        birdeye_client: BirdeyeClient,
    ):
        self.rugcheck_client = rugcheck_client
        self.birdeye_client = birdeye_client
        self.metrics = SecurityMetrics()

    async def analyze_token(self, token: Token) -> Dict[str, float]:
        """
        Perform a comprehensive security analysis of a token.
        Returns a dict of security metrics.
        """
        if not validate_solana_address(token.address):
            logger.error(f"Invalid token address: {token.address}")
            return {"security_score": 0.0}

        tasks = [
            self._check_contract_safety(token.address),
            self._analyze_holder_distribution(token.address),
            self._check_liquidity_status(token.address)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        contract_score, holder_score, liquidity_score = 0.0, 0.0, 0.0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in security analysis task {i}: {result}")
                continue
            if i == 0:
                contract_score = result
            elif i == 1:
                holder_score = result
            elif i == 2:
                liquidity_score = result

        security_score = self._calculate_final_score(
            contract_score, holder_score, liquidity_score
        )

        return {
            "security_score": security_score,
            "contract_score": contract_score,
            "holder_score": holder_score,
            "liquidity_score": liquidity_score
        }

    async def _check_contract_safety(self, address: str) -> float:
        """Check contract safety using Rugcheck."""
        try:
            safety_data = await self.rugcheck_client.check_token(address)
            if not safety_data:
                return 0.0

            score = 1.0
            
            # Deduct points for security issues
            if safety_data.get("mint_authority_enabled", True):
                score -= 0.3
            if safety_data.get("freeze_authority_enabled", True):
                score -= 0.2
            if not safety_data.get("is_verified", False):
                score -= 0.2
            
            self.metrics.record_contract_safety_score(address, score)
            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error checking contract safety: {e}")
            return 0.0

    async def _analyze_holder_distribution(self, address: str) -> float:
        """Analyze token holder distribution using Birdeye."""
        try:
            holders = await self.birdeye_client.get_token_holders(address)
            if not holders:
                return 0.0

            score = 1.0
            total_supply = sum(h["amount"] for h in holders)
            
            # Check concentration
            for holder in holders:
                percentage = (holder["amount"] / total_supply) * 100
                if percentage > 20:  # Single holder owns >20%
                    score -= 0.3
                    break
            
            self.metrics.record_holder_distribution_score(address, score)
            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error analyzing holder distribution: {e}")
            return 0.0

    async def _check_liquidity_status(self, address: str) -> float:
        """Check liquidity status and lock using Birdeye."""
        try:
            token_data = await self.birdeye_client.get_token_data(address)
            if not token_data:
                return 0.0

            score = 1.0
            
            # Check liquidity
            liquidity = token_data.get("liquidity", 0)
            if liquidity < 1000:  # Less than $1000 liquidity
                score -= 0.5
            elif liquidity < 5000:  # Less than $5000 liquidity
                score -= 0.3
            
            self.metrics.record_liquidity_score(address, score)
            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error checking liquidity status: {e}")
            return 0.0

    def _calculate_final_score(
        self,
        contract_score: float,
        holder_score: float,
        liquidity_score: float
    ) -> float:
        """Calculate final security score with weighted components."""
        weights = {
            "contract": 0.4,    # Contract safety is most important
            "holders": 0.3,     # Holder distribution next
            "liquidity": 0.3    # Liquidity status
        }
        
        final_score = (
            contract_score * weights["contract"] +
            holder_score * weights["holders"] +
            liquidity_score * weights["liquidity"]
        )
        
        return round(final_score, 2)
