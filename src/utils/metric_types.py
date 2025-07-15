"""Type definitions for metric labels."""
from typing import Literal

TokenUpdateStatus = Literal["added", "updated", "error", "validation_failed"]
MonitorOperation = Literal[
    "store_data",
    "broadcast",
    "market_data",
    "momentum_analysis",
    "monitor_loop",
    "price_update"
]
