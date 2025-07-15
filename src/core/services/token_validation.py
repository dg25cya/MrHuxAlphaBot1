"""Token validation service with enhanced checks and retries."""
from typing import Dict, Optional, Tuple
import asyncio
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ...config.settings import get_settings
from ...api.clients.rugcheck import RugcheckClient
from ...api.clients.dexscreener import DexscreenerClient
from ...api.clients.birdeye import BirdeyeClient
from ...utils.solana_utils import is_valid_solana_address
from ...core.monitoring import TOKEN_VALIDATION_COUNT, PROM_TOKEN_VALIDATIONS

settings = get_settings()

class TokenValidationError(Exception):
    """Base exception for token validation errors."""
    pass

class TokenValidationService:
    """Service for validating Solana tokens with multiple API checks and retries."""
    
    def __init__(self) -> None:
        """Initialize the token validation service."""
        self.rugcheck = RugcheckClient()
        self.dexscreener = DexscreenerClient()
        self.birdeye = BirdeyeClient()
        
        # Configure validation thresholds
        self.min_liquidity = settings.min_liquidity_usd
        self.max_owner_percentage = settings.whale_holder_threshold
        self.min_holders = getattr(settings, 'min_token_holders', 100)  # Default to 100 if not set
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def validate_contract_safety(self, token_address: str) -> Dict:
        """Validate contract safety using Rugcheck."""
        if not is_valid_solana_address(token_address):
            raise TokenValidationError("Invalid Solana address format")
        
        safety_data = await self.rugcheck.check_token(token_address)
        
        if not safety_data:
            raise TokenValidationError("Unable to fetch safety data")
        
        return safety_data
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def check_liquidity_and_holders(
        self,
        token_address: str
    ) -> Tuple[float, int]:
        """Check token liquidity and holder count."""
        # Get data from both Dexscreener and Birdeye for validation
        dex_data = await self.dexscreener.get_token_data(token_address)
        birdeye_data = await self.birdeye.get_token_metadata(token_address)
        
        # Use the most conservative estimates for liquidity
        liquidity = min(
            dex_data.get("liquidity", 0),
            birdeye_data.get("liquidity", 0) if isinstance(birdeye_data, dict) else 0
        )
        
        # Only use Birdeye for holder count since Dexscreener doesn't provide it
        holders = birdeye_data.get("holders", 0) if isinstance(birdeye_data, dict) else 0
        
        return liquidity, holders
    
    async def get_owner_concentration(
        self,
        token_address: str
    ) -> Optional[float]:
        """Get the percentage of tokens held by top holders."""
        try:
            holder_data = await self.birdeye.get_token_holders(token_address)
            if not holder_data:
                return None
            
            total_supply = sum(h.get("balance", 0) for h in holder_data)
            if not total_supply:
                return None
            
            top_holder_balance = max(h.get("balance", 0) for h in holder_data)
            return (top_holder_balance / total_supply) * 100
        except Exception as e:
            logger.warning(f"Error getting owner concentration: {e}")
            return None
    
    async def validate_token(
        self,
        token_address: str,
        required_checks: Optional[Dict[str, bool]] = None
    ) -> Dict:
        """
        Validate a token against all safety and quality metrics.
        
        Args:
            token_address: The token's contract address
            required_checks: Dict of required check names and their required status
        
        Returns:
            Dict containing validation results and metrics
        """
        # Use Prometheus counter instead of .inc() method
        PROM_TOKEN_VALIDATIONS.labels(status="attempt").inc()
        
        # Also record in our custom metrics object for backward compatibility
        TOKEN_VALIDATION_COUNT.record_validation(
            success=False,  # Will update to True if successful
            source="validation_service"
        )
        
        if required_checks is None:
            required_checks = {
                "contract_safety": True,
                "liquidity": True,
                "holders": True,
                "ownership": True
            }
        
        results = {
            "address": token_address,
            "is_valid": False,
            "checks": {},
            "metrics": {}
        }
        
        try:
            # Run all validation checks concurrently
            safety_task = asyncio.create_task(
                self.validate_contract_safety(token_address)
            )
            liquidity_task = asyncio.create_task(
                self.check_liquidity_and_holders(token_address)
            )
            ownership_task = asyncio.create_task(
                self.get_owner_concentration(token_address)
            )
            
            # Wait for all checks to complete
            safety_data = await safety_task
            liquidity, holders = await liquidity_task
            owner_percentage = await ownership_task
            
            # Process contract safety
            results["checks"]["contract_safety"] = {
                "passed": safety_data.get("is_safe", False),
                "required": required_checks.get("contract_safety", True)
            }
            results["metrics"]["safety_score"] = safety_data.get("safety_score", 0)
            
            # Process liquidity
            has_liquidity = liquidity >= self.min_liquidity
            results["checks"]["liquidity"] = {
                "passed": has_liquidity,
                "required": required_checks.get("liquidity", True)
            }
            results["metrics"]["liquidity"] = liquidity
            
            # Process holders
            has_holders = holders >= self.min_holders
            results["checks"]["holders"] = {
                "passed": has_holders,
                "required": required_checks.get("holders", True)
            }
            results["metrics"]["holders"] = holders
            
            # Process ownership concentration
            if owner_percentage is not None:
                has_safe_ownership = owner_percentage <= self.max_owner_percentage
                results["checks"]["ownership"] = {
                    "passed": has_safe_ownership,
                    "required": required_checks.get("ownership", True)
                }
                results["metrics"]["owner_percentage"] = owner_percentage
            
            # Determine overall validity
            required_checks_passed = all(
                check["passed"] or not check["required"]
                for check in results["checks"].values()
            )
            
            results["is_valid"] = required_checks_passed
            
            # Update metrics for successful validation
            if results["is_valid"]:
                PROM_TOKEN_VALIDATIONS.labels(status="success").inc()
                TOKEN_VALIDATION_COUNT.record_validation(
                    success=True,
                    source="validation_service"
                )
            else:
                PROM_TOKEN_VALIDATIONS.labels(status="failed").inc()
            
        except Exception as e:
            logger.exception(f"Error validating token {token_address}: {e}")
            results["error"] = str(e)
            PROM_TOKEN_VALIDATIONS.labels(status="error").inc()
        
        return results
