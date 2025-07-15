"""Decimal utility functions."""
from decimal import Decimal
from typing import Union


def decimal_abs(value: Union[Decimal, int, float]) -> Decimal:
    """Get absolute value of a Decimal."""
    return abs(Decimal(str(value)))


def decimal_max(*values: Union[Decimal, int, float]) -> Decimal:
    """Get maximum of Decimal values."""
    return max(Decimal(str(v)) for v in values)


def decimal_min(*values: Union[Decimal, int, float]) -> Decimal:
    """Get minimum of Decimal values."""
    return min(Decimal(str(v)) for v in values)


def decimal_round(value: Union[Decimal, int, float], places: int = 2) -> Decimal:
    """Round Decimal to specified number of places."""
    return Decimal(str(value)).quantize(Decimal(10) ** -places)


def decimal_to_percent(value: Union[Decimal, int, float]) -> Decimal:
    """Convert decimal to percentage."""
    return Decimal(str(value)) * 100


def percent_to_decimal(value: Union[Decimal, int, float]) -> Decimal:
    """Convert percentage to decimal."""
    return Decimal(str(value)) / 100
