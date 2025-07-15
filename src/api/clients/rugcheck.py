"""Rugcheck API client implementation."""
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from loguru import logger

from .base import BaseAPIClient, retry_on_error
from ...config.settings import get_settings

settings = get_settings()

class SecurityScore(BaseModel):
    """Token security score and analysis."""
    address: str
    total_score: float
    liquidity_score: float
    contract_score: float
    holder_score: float
    is_contract_verified: bool
    is_proxy_contract: bool
    has_mint_function: bool
    has_blacklist_function: bool
    owner_balance_percent: float
    top_holders_percent: float
    is_honeypot: bool
    sell_tax: float
    buy_tax: float
    updated_at: datetime

class RugcheckClient(BaseAPIClient):
    """Client for Rugcheck API."""

    def __init__(self) -> None:
        super().__init__(
            name="rugcheck",
            base_url="https://api.rugcheck.xyz/v1",
            rate_limit_calls=100,
            rate_limit_period=60.0,
            cache_ttl=300  # 5 minutes cache for security data
        )
        self.api_key = settings.rugcheck_api_key

    @retry_on_error(max_retries=3)
    async def get_security_score(self, address: str) -> SecurityScore:
        """Get comprehensive security analysis for a token."""
        endpoint = f"/token/scan"
        cache_key = f"security_{address}"
        response = await self._make_request(
            method="POST",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )
        
        return SecurityScore(**response)

    @retry_on_error(max_retries=3)
    async def get_holder_analysis(self, address: str) -> Dict[str, Any]:
        """Get detailed holder analysis."""
        endpoint = f"/token/holders"
        cache_key = f"holders_{address}"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    @retry_on_error(max_retries=3)
    async def get_contract_analysis(self, address: str) -> Dict[str, Any]:
        """Get detailed contract analysis."""
        endpoint = f"/token/contract"
        cache_key = f"contract_{address}"
        
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            params={"address": address},
            headers={"X-API-KEY": self.api_key},
            cache_key=cache_key
        )

    @retry_on_error(max_retries=3)
    async def get_mint_info(self, token_address: str) -> Dict[str, Any]:
        """Get token mint authority information."""
        cache_key = f"mint_{token_address}"
        endpoint = f"/token/{token_address}/mint"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint
        )

        return {
            'disabled': bool(response.get('is_mint_disabled')),
            'authority': response.get('mint_authority'),
            'last_updated': response.get('last_checked_at')
        }

    @retry_on_error(max_retries=3)
    async def get_lp_info(self, token_address: str) -> Dict[str, Any]:
        """Get liquidity pool information."""
        cache_key = f"lp_{token_address}"
        endpoint = f"/token/{token_address}/liquidity"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint
        )

        pairs = []
        total_liquidity = Decimal('0')
        
        for pair in response.get('pairs', []):
            liquidity = Decimal(str(pair.get('total_liquidity', '0')))
            total_liquidity += liquidity
            
            pairs.append({
                'address': pair.get('address'),
                'dex': pair.get('dex'),
                'liquidity': float(liquidity),
                'lock_time_days': pair.get('lock_time_days', 0),
                'is_locked': bool(pair.get('is_locked'))
            })
        
        return {
            'pairs': pairs,
            'total_liquidity': float(total_liquidity)
        }

    @retry_on_error(max_retries=3)
    async def get_audit_info(self, token_address: str) -> Dict[str, Any]:
        """Get contract audit information."""
        cache_key = f"audit_{token_address}"
        endpoint = f"/token/{token_address}/audit"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint
        )

        return {
            'has_audit': bool(response.get('has_audit')),
            'audit_date': response.get('audit_date'),
            'auditor': response.get('auditor'),
            'critical_issues': response.get('critical_issues', 0),
            'major_issues': response.get('major_issues', 0),
            'minor_issues': response.get('minor_issues', 0)
        }

    @retry_on_error(max_retries=3)
    async def get_tax_info(self, token_address: str) -> Dict[str, Any]:
        """Get token tax and fee information."""
        cache_key = f"tax_{token_address}"
        endpoint = f"/token/{token_address}/tax"

        response = await self._make_request(
            method="GET",
            endpoint=endpoint
        )

        return {
            'buy_tax': str(response.get('buy_tax', '0')),
            'sell_tax': str(response.get('sell_tax', '0')),
            'transfer_tax': str(response.get('transfer_tax', '0')),
            'last_updated': response.get('last_checked_at')
        }

    @retry_on_error(max_retries=3)
    async def check_token(self, token_address: str) -> Dict[str, Any]:
        """Check token for safety and provide validation data.
        
        This method combines multiple checks to provide a complete safety profile.
        """
        try:
            # Get the security score first
            security = await self.get_security_score(token_address)
            
            # Combine with mint info
            mint_info = await self.get_mint_info(token_address)
            
            # Get LP information
            lp_info = await self.get_lp_info(token_address)
            
            # Get tax information
            tax_info = await self.get_tax_info(token_address)
            
            # Create a comprehensive safety report
            return {
                "address": token_address,
                "is_safe": security.total_score >= 70.0,
                "safety_score": security.total_score,
                "is_mint_disabled": mint_info.get("disabled", False),
                "mint_authority": mint_info.get("authority"),
                "total_liquidity": lp_info.get("total_liquidity", 0),
                "is_lp_locked": any(pair.get("is_locked", False) for pair in lp_info.get("pairs", [])),
                "buy_tax": float(tax_info.get("buy_tax", "0")),
                "sell_tax": float(tax_info.get("sell_tax", "0")),
                "is_honeypot": security.is_honeypot,
                "owner_percentage": security.owner_balance_percent,
                "top_holders_percentage": security.top_holders_percent,
                "has_mint_function": security.has_mint_function,
                "is_contract_verified": security.is_contract_verified,
            }
        except Exception as e:
            # Return a basic structure with error information
            return {
                "address": token_address,
                "is_safe": False,
                "safety_score": 0,
                "error": str(e)
            }

    async def _check_health_endpoint(self):
        """Check API health using a test token."""
        test_token = "RAY27yZqDJQYVRGz1kPYxyYmRdZxhx5FcrWzJ2pc4TZ"  # Raydium token
        await self.get_security_score(test_token)

    async def check_status(self) -> bool:
        """Check if the Rugcheck API is working properly."""
        try:
            await self._check_health_endpoint()
            return True
        except Exception as e:
            logger.error(f"Rugcheck API status check failed: {e}")
            return False
