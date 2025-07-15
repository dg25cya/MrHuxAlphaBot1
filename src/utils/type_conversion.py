"""Utilities for safe type conversion."""
from typing import Union, Optional
from decimal import Decimal
from sqlalchemy import Column

def safe_float(value: Union[str, int, float, Decimal, Column]) -> float:
    """Safely convert a value to float."""
    if isinstance(value, Column):
        value = str(value)
    try:
        if isinstance(value, str):
            return float(value.strip())
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_int(value: Union[str, int, float, Decimal, Column]) -> int:
    """Safely convert a value to int."""
    if isinstance(value, Column):
        value = str(value)
    try:
        if isinstance(value, str):
            return int(float(value.strip()))
        if isinstance(value, float):
            return int(value)
        return int(value)
    except (ValueError, TypeError):
        return 0
