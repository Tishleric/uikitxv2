"""Data models for P&L calculation.

This module contains the core data structures used in P&L calculations:
- Trade: Represents a single trade transaction
- Lot: Represents a position lot for FIFO tracking
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Trade:
    """Represents a single trade transaction.
    
    Attributes:
        timestamp: When the trade occurred
        symbol: Trading symbol (e.g., 'AAPL', 'MSFT')
        quantity: Trade quantity (positive for buy, negative for sell)
        price: Execution price per unit
        trade_id: Optional unique identifier for the trade
    """
    timestamp: datetime
    symbol: str
    quantity: float  # Positive for buy, negative for sell
    price: float
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade data after initialization."""
        if self.quantity == 0:
            raise ValueError("Trade quantity cannot be zero")
        if self.price < 0:
            raise ValueError("Trade price cannot be negative")
        if not self.symbol:
            raise ValueError("Trade symbol cannot be empty")


@dataclass
class Lot:
    """Represents a position lot for FIFO tracking.
    
    A lot is a specific quantity of an asset acquired at a specific price
    on a specific date. Used for FIFO (First-In-First-Out) position tracking.
    
    Attributes:
        quantity: Lot size (positive for long, negative for short)
        price: Acquisition price per unit
        date: Date when the lot was created
    """
    quantity: float
    price: float
    date: date
    
    def __post_init__(self):
        """Validate lot data after initialization."""
        if self.quantity == 0:
            raise ValueError("Lot quantity cannot be zero")
        if self.price < 0:
            raise ValueError("Lot price cannot be negative") 