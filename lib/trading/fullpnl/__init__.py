"""
FULLPNL Master P&L Table Automation

This package provides automated building and maintenance of the FULLPNL master P&L table,
consolidating data from multiple sources:
- Positions and trades from pnl_tracker.db
- Greeks and market data from spot_risk.db  
- Market prices from market_prices.db
"""

# Import classes when they're ready
# These will be imported after all modules are implemented
# from .builder import FULLPNLBuilder
# from .symbol_mapper import SymbolMapper
# from .data_sources import PnLDatabase, SpotRiskDatabase, MarketPricesDatabase

# For now, expose what's implemented
try:
    from .symbol_mapper import SymbolMapper
except ImportError:
    pass

try:
    from .data_sources import PnLDatabase, SpotRiskDatabase, MarketPricesDatabase
except ImportError:
    pass

try:
    from .builder import FULLPNLBuilder
except ImportError:
    pass

__version__ = "1.0.0"
__all__ = [
    "FULLPNLBuilder",
    "SymbolMapper", 
    "PnLDatabase",
    "SpotRiskDatabase",
    "MarketPricesDatabase",
] 