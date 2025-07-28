# Close Price Watcher Implementation

## Overview

The Close Price Watcher monitors `Z:\Trade_Control\Futures` and `Z:\Trade_Control\Options` directories for new CSV files containing close prices, and updates the pricing table in `trades.db`.

## Key Features

1. **New Files Only**: Processes only new CSV files (ignores existing/historical files)
2. **Real-time Updates**: Calls `roll_2pm_prices()` for every CSV received
3. **Smart 4pm Roll**: Triggers `roll_4pm_prices()` either:
   - At exactly 4:00pm CDT if all 3 daily files received (2pm, 3pm, 4pm)
   - At 4:30pm CDT if at least the 4pm file is received (fallback)
4. **CDT Timezone Aware**: All time calculations use Chicago timezone

## File Format

### Futures CSV Format
- **Row Check**: H2-H6 contain status ('Y' for settle, 'N' for flash)
- **Symbol Column**: A2-A6 contain base symbols (TU, FV, TY, US, RX)
- **Price Columns**: 
  - B2-B6: Settlement prices (used when status='Y')
  - C2-C6: Flash close prices (used when status='N')

### Options CSV Format
- **Status Check**: G2 contains status ('Y' for settle, 'N' for flash)
- **Symbol Column**: I2-I433 contain full Bloomberg symbols
- **Price Columns**:
  - K2-K433: Settlement prices (used when G2='Y')
  - J2-J433: Flash close prices (used when G2='N')

## Implementation Details

### Module Structure
- `lib/trading/pnl_fifo_lifo/close_price_watcher.py` - Main implementation
- `lib/trading/pnl_fifo_lifo/config.py` - Configuration and symbol mappings
- `scripts/run_close_price_watcher.py` - Run script

### Key Classes

1. **DailyCSVTracker**: Tracks files received per trading day
   - Thread-safe tracking of received files
   - Determines when to trigger 4pm roll

2. **ClosePriceFileHandler**: Processes CSV files
   - Parses futures and options formats
   - Updates pricing table via `roll_2pm_prices()`
   - Background thread monitors for 4pm roll conditions

3. **ClosePriceWatcher**: Main watcher class
   - Manages file system observers
   - Coordinates file processing

## Configuration

In `lib/trading/pnl_fifo_lifo/config.py`:

```python
CLOSE_PRICE_WATCHER = {
    'futures_dir': r'Z:\Trade_Control\Futures',
    'options_dir': r'Z:\Trade_Control\Options',
    'expected_times': [14, 15, 16],  # 2pm, 3pm, 4pm CDT
    'roll_4pm_time': 16,  # 4pm CDT
    'final_roll_cutoff': 16.5,  # 4:30pm CDT
    'process_existing': False
}

FUTURES_SYMBOLS = {
    'TU': 'TUU5 Comdty',  # 2-year
    'FV': 'FVU5 Comdty',  # 5-year
    'TY': 'TYU5 Comdty',  # 10-year
    'US': 'USU5 Comdty',  # Ultra Bond
    'RX': 'RXU5 Comdty'   # Euro-Bund
}
```

## Usage

### Running Standalone
```bash
python scripts/run_close_price_watcher.py --db trades.db --log-level INFO
```

### Running with All Watchers
```bash
run_all_pnl_watchers.bat
```

## Integration with P&L System

1. **Price Updates**: Every CSV triggers `roll_2pm_prices()` which:
   - Updates 'close' price in pricing table
   - Copies to 'sodTom' (Start of Day Tomorrow)

2. **4pm Roll**: When conditions met, `roll_4pm_prices()`:
   - Moves 'sodTom' → 'sodTod' (preserving timestamp)
   - Clears 'sodTom'

3. **Dynamic P&L**: Unrealized P&L calculations automatically use latest prices from pricing table

## Logging

- Logs written to `logs/close_price_watcher_YYYYMMDD_HHMM.log`
- Includes price updates, file processing status, and 4pm roll events
- Debug mode available with `--log-level DEBUG`

## Error Handling

- Waits for files to be fully written before processing
- Handles invalid prices (#NAME? values)
- Thread-safe file tracking prevents duplicate processing
- Graceful shutdown on Ctrl+C

## Migration Notes

This watcher replaces the deprecated `run_corrected_market_price_monitor.py` which updated the old `market_prices.db`. The new implementation:
- Updates `trades.db` directly
- Uses the new CSV format
- Integrates with FIFO/LIFO P&L calculations 