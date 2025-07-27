# File Watchers and Processing Pipelines Context

## System Overview

This document provides a comprehensive overview of all file watchers and processing pipelines in the UIKitXv2 trading system. The system uses multiple coordinated watchers to monitor file changes and trigger appropriate data processing pipelines.

## Active File Watchers

### 1. Market Price File Monitor
**Location**: `lib/trading/market_prices/file_monitor.py`
**Purpose**: Monitors for new futures and options price files
**Watches**: 
- `data/input/market_prices/futures/` (*.csv files)
- `data/input/market_prices/options/` (*.csv files)
**Triggers**: Updates to `market_prices.db` with futures and options pricing data
**Schedule**: Continuous monitoring, processes files based on timestamps (2pm/4pm Chicago time)

### 2. Spot Risk Watcher
**Location**: `lib/trading/actant/spot_risk/file_watcher.py`
**Purpose**: Processes Actant spot risk CSV files containing current positions and Greeks
**Watches**: `data/input/actant_spot_risk/`
**Outputs**: 
- Processed CSVs in `data/output/spot_risk/`
- Updates current prices in `spot_risk.db`
**Triggers**: FULLPNL table updates when new spot risk data arrives

### 3. PNL Pipeline Watcher
**Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py`
**Purpose**: Central orchestrator that monitors multiple sources and triggers P&L calculations
**Monitors**:
- Trade ledger files: `data/input/trade_ledger/trades_*.csv`
- Market prices database: `data/output/market_prices/market_prices.db`
- Spot risk files: `data/output/spot_risk/*.csv`
**Triggers**:
- TYU5 P&L pipeline when trade ledgers or market prices change
- FULLPNL updates when spot risk files change

### 4. EOD P&L Monitor
**Location**: `lib/trading/pnl_integration/eod_snapshot_service.py`
**Purpose**: Monitors for 4pm settlement prices and calculates end-of-day P&L snapshots
**Watches**: `market_prices.db` for settlement price updates
**Schedule**: Active 3pm-6pm Chicago time, checks every 60 seconds
**Outputs**: EOD P&L snapshots in `tyu5_eod_pnl_history` table

### 5. Lot Snapshot Monitor (2PM)
**Location**: `lib/trading/pnl_integration/lot_snapshot_service.py`
**Purpose**: Captures position snapshots at 2pm Chicago time for P&L period calculations
**Schedule**: Checks every minute for 2pm snapshot requirement
**Outputs**: Position snapshots in `tyu5_lot_snapshots` table

## Processing Pipelines

### TYU5 P&L Pipeline
**Trigger**: Trade ledger changes or market price updates
**Flow**:
1. **Trade Preprocessing**: `TradePreprocessor` → `processed_trades` table
2. **TYU5 Calculation**: 
   - Loads trades from CSV or database
   - Applies market prices (current, flash, settlement)
   - Calculates positions, P&L components, and risk metrics
3. **Database Persistence**: Results saved to:
   - `tyu5_trades`
   - `tyu5_positions` 
   - `tyu5_pnl_components`
   - `tyu5_risk_matrix`
4. **FULLPNL Update**: Merges TYU5 positions with spot risk Greeks

### FULLPNL Builder Pipeline
**Trigger**: Spot risk file updates or TYU5 calculations
**Flow**:
1. Load latest TYU5 positions from database
2. Load latest spot risk data with Greeks
3. Map symbols between TYU5 (CME format) and spot risk (Bloomberg format)
4. Merge data and apply price precision rules (6 decimal places)
5. Write to `FULLPNL` table for dashboard display

### EOD Snapshot Pipeline
**Trigger**: 4pm settlement price availability
**Flow**:
1. Detect 4pm price batch completion
2. Calculate P&L for the period ending at 2pm today
3. Aggregate P&L components using SQL
4. Store snapshot in `tyu5_eod_pnl_history`
5. Update cumulative P&L tracking

## Running the Watchers

### Unified Watcher Service (Recommended)
```bash
python scripts/run_all_watchers.py
```
This starts all watchers in coordinated threads with proper logging.

### Individual Watchers
```bash
# Trade ledger and market price monitoring
python scripts/run_trade_ledger_watcher.py

# Spot risk monitoring only
python scripts/run_spot_risk_watcher.py

# EOD monitoring (3pm-6pm window)
python scripts/run_eod_monitor.py
```

### Force Reprocessing
When watchers mark existing files as "processed" on startup:
```bash
# Force reprocess all data
python scripts/force_pnl_reprocessing.py

# Reprocess specific components
python scripts/force_pnl_reprocessing.py --tyu5    # TYU5 only
python scripts/force_pnl_reprocessing.py --fullpnl  # FULLPNL only
```

## Key Design Decisions

### File Processing State
- Watchers track processed files using modification time to prevent reprocessing
- On startup, existing files are marked as "processed" to avoid triggering
- Only NEW or MODIFIED files after startup trigger processing

### Debouncing
- Trade ledger changes: 10-second debounce
- Spot risk changes: 10-second debounce  
- Market price checks: 10-second intervals

### P&L Period Convention
- P&L periods run 2pm to 2pm Chicago time
- At 4pm on Tuesday, calculate P&L for Monday 2pm to Tuesday 2pm
- Settlement prices from market close are used for valuation

### Database Tables
**P&L Tracker DB** (`data/output/pnl/pnl_tracker.db`):
- `tyu5_trades`: Individual trades with FIFO matching
- `tyu5_positions`: Current positions with P&L
- `tyu5_pnl_components`: P&L breakdown by settlement period
- `tyu5_eod_pnl_history`: Daily EOD snapshots
- `FULLPNL`: Combined positions with Greeks for display

**Market Prices DB** (`data/output/market_prices/market_prices.db`):
- `futures_prices`: Futures pricing data
- `options_prices`: Options pricing data with Greeks

## Common Issues and Solutions

### Issue: Existing files not processed
**Solution**: Use `force_pnl_reprocessing.py` or touch files to update modification time

### Issue: Database locked errors
**Solution**: Ensure only one watcher instance is running; databases use WAL mode

### Issue: Missing settlement prices
**Solution**: Check market price files for 4pm timestamps; system reports missing prices explicitly

### Issue: Symbol mapping mismatches
**Solution**: Verify ExpirationCalendar.csv mappings; check centralized symbol translator

## Architecture Diagram

```
Trade Files → Trade Ledger Watcher → TYU5 Pipeline → Database
                                            ↓
Market Prices → Price Monitor →→→→→→→→→→→→→↘
                                            ↓
Spot Risk → Spot Risk Watcher → Greeks →→→ FULLPNL → Dashboard
                                            ↓
Settlement Prices (4pm) → EOD Monitor → EOD History
```

## Monitoring and Logs

All watchers log to console with format:
```
TIMESTAMP - MODULE - LEVEL - MESSAGE
```

Key log locations to monitor:
- Pipeline triggers: Look for "Triggering TYU5 pipeline"
- Processing success: "Successfully wrote N tables to database"
- EOD snapshots: "EOD snapshot completed for P&L date"
- Errors: "Error in [component]"

## For New Developers

1. **Start Here**: Run `python scripts/check_pnl_processing_status.py` to see current state
2. **Reset If Needed**: Use `python scripts/reset_pnl_processing.py` to clear and restart
3. **Run Watchers**: Use `python scripts/run_all_watchers.py` for full monitoring
4. **Force Process**: Use `python scripts/force_pnl_reprocessing.py` when needed
5. **Check Results**: Query `FULLPNL` table or view FRGMonitor dashboard

## Related Documentation

- `memory-bank/activeContext.md` - Current project focus
- `lib/trading/pnl_integration/README.md` - TYU5 integration details
- `docs/actant_symbol_format_guide.md` - Symbol format specifications 