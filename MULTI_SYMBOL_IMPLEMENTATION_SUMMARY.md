# Multi-Symbol P&L Simulation Implementation Summary

## Changes Made

The P&L FIFO/LIFO test simulation has been upgraded to support multiple symbols with different closing prices on the same day. This was achieved through the following modifications:

### 1. Data Manager Changes (`lib/trading/pnl_fifo_lifo/data_manager.py`)

- **Modified `setup_pricing_as_of` function:**
  - Changed signature from `setup_pricing_as_of(conn, valuation_datetime, close_prices, current_price, symbol)` 
    to `setup_pricing_as_of(conn, valuation_datetime, close_prices, symbol)`
  - Updated to accept nested dictionary structure: `close_prices[date][symbol] = price`
  - Added logic to find dates with prices for specific symbols
  - Derives current_price from the close_prices dictionary

- **Modified `view_unrealized_positions` function:**
  - Added optional `symbol` parameter to filter positions by symbol
  - Enables calculation of unrealized P&L for specific symbols only

### 2. Test Simulation Changes (`lib/trading/pnl_fifo_lifo/test_simulation.py`)

- **Modified `run_comprehensive_daily_breakdown` function:**
  - Added optional `close_prices` parameter to accept custom price dictionaries
  - Converts old single-symbol format to new multi-symbol format for backward compatibility
  - Updated end-of-day processing to:
    1. Get all unique symbols with open positions
    2. Process each symbol individually with its own closing price
    3. Store unrealized P&L by date AND symbol
  - Updated reporting logic to sum P&L across all symbols for daily totals

### 3. Usage Example

The new functionality can be used as follows:

```python
from datetime import datetime
from lib.trading.pnl_fifo_lifo.test_simulation import run_comprehensive_daily_breakdown

# Define prices for multiple symbols
multi_symbol_prices = {
    datetime(2025, 7, 25).date(): {
        'XCMEFFDPSX20250919U0ZN': 110.984375,  # Futures
        'XCMEOCADPS20250919Q0TY4': 2.10,       # Options
    },
    # ... more dates
}

# Run simulation with multi-symbol support
run_comprehensive_daily_breakdown(close_prices=multi_symbol_prices)
```

## Key Features

1. **Backward Compatible**: If no close_prices are provided, it uses default single-symbol prices
2. **Flexible**: Can handle any number of symbols with different prices per day
3. **Comprehensive**: Each symbol gets its own P&L calculation with correct historical prices
4. **Transparent**: Warns when a symbol has trades but no closing price for a given day

## Testing

A test script `test_multi_symbol_functionality.py` has been created to verify the implementation works correctly.

## Next Steps

To use this for your specific case with options trades:

1. Prepare your close prices dictionary with both futures and options symbols
2. Ensure your trade CSV files contain the correct symbol identifiers
3. Run the simulation using the new multi-symbol format

The database will be rebuilt with accurate P&L calculations for each instrument using their respective closing prices.