# DEPRECATED - Market Prices Module

**This module has been deprecated as of 2024-01-20**

## Replacement
The functionality of this module has been replaced by:
- `lib/trading/pnl_fifo_lifo/close_price_watcher.py` - For close price monitoring
- Updates now go directly to `trades.db` instead of `market_prices.db`

## Migration Notes
- The new Close Price Watcher monitors the same directories (Z:\Trade_Control\Futures and Options)
- Uses the new CSV format with different column mappings
- Integrates directly with the FIFO/LIFO P&L system

## Files in this module
- `file_monitor.py` - DEPRECATED
- `futures_processor.py` - DEPRECATED  
- `options_processor.py` - DEPRECATED
- `storage.py` - DEPRECATED (used market_prices.db)
- `run_corrected_market_price_monitor.py` - DEPRECATED

**DO NOT USE THIS MODULE FOR NEW DEVELOPMENT** 