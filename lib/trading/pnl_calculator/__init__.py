"""P&L Calculator module for FIFO-based profit and loss calculations.

This module provides comprehensive P&L calculation functionality including:
- FIFO (First-In-First-Out) position tracking
- Realized and unrealized P&L calculations
- Support for long and short positions
- Daily P&L breakdowns
- Storage layer for persistence
- File watching for real-time updates
- Service layer for orchestration
"""

from .models import Trade, Lot
from .calculator import PnLCalculator
from .storage import PnLStorage
from .watcher import PnLFileWatcher
from .service import PnLService
from .controller import PnLController

__all__ = [
    "Trade", 
    "Lot", 
    "PnLCalculator",
    "PnLStorage",
    "PnLFileWatcher",
    "PnLService",
    "PnLController"
] 