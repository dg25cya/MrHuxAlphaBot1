"""Token safety data models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TokenSafetyData(BaseModel):
    """Token safety data from RugCheck."""
    is_valid: bool = False
    holders_count: Optional[int] = None
    buy_tax: Optional[float] = None
    sell_tax: Optional[float] = None
    contract_verified: bool = False
    creator_address: Optional[str] = None
    creator_balance_percentage: Optional[float] = None
    is_honeypot: bool = False
    is_blacklisted: bool = False
    is_proxy: bool = False
    is_mintable: bool = False
    ownership_renounced: bool = False
    errors: list[str] = []
    checked_at: datetime
