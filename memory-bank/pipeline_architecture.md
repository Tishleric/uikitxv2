# Pipeline Architecture Documentation

## Overview
This document provides a comprehensive view of all active data pipelines and file watchers in the uikitxv2 trading system as of July 21, 2025.

## Active Pipelines

### 1. Market Price Pipeline
**Purpose**: Ingest and process market price data from multiple sources

#### Components:
- **MarketPriceFileMonitor** (`lib/trading/market_prices/file_monitor.py`)
  - Monitors: `data/input/market_prices/futures/` and `data/input/market_prices/options/`
  - Processing windows: 2pm CDT (Current_Price) and 4pm CDT (Prior_Close)
  - Output: `market_prices` table in `data/output/market_prices/market_prices.db`

- **SpotRiskPriceProcessor** (via SpotRiskWatcher)
  - Source: Spot risk CSV files containing ADJTHEOR values
  - Updates: Current_Price column in market_prices.db
  - Fallback: Uses (BID+ASK)/2 when ADJTHEOR unavailable

#### Data Flow:
```
Bloomberg CSV files (2pm/4pm) → MarketPriceFileMonitor → market_prices.db
Spot Risk CSV files → SpotRiskWatcher → SpotRiskPriceProcessor → market_prices.db
```

### 2. Spot Risk Pipeline
**Purpose**: Process spot risk files for Greek calculations and current market prices

#### Components:
- **SpotRiskWatcher** (`lib/trading/actant/spot_risk/file_watcher.py`)
  - Monitors: `data/input/actant_spot_risk/`
  - Dual output:
    1. Greek calculations → `data/output/spot_risk/` (CSV files)
    2. Current prices → `market_prices.db` (via SpotRiskPriceProcessor)

#### Data Flow:
```
Spot Risk CSV → SpotRiskWatcher → Calculator → Greek CSVs
                              ↓
                    SpotRiskPriceProcessor → market_prices.db
```

### 3. TYU5 P&L Pipeline
**Purpose**: Calculate comprehensive P&L using TYU5 engine

#### Components:
- **PNLPipelineWatcher** (`lib/trading/pnl_integration/pnl_pipeline_watcher.py`)
  - Monitors: 
    - Trade ledger files: `data/input/trade_ledger/trades_*.csv`
    - Market prices database changes
  - Triggers: TYU5 P&L calculation on any change

- **TradeLedgerAdapter** (`lib/trading/pnl_integration/trade_ledger_adapter.py`)
  - Reads ALL trade ledger CSVs (not just most recent)
  - Filters: zero-price trades and midnight trades
  - Symbol translation: XCME → Bloomberg format

- **TYU5Runner** (`lib/trading/pnl_integration/tyu5_runner.py`)
  - Executes TYU5 P&L calculations
  - Returns DataFrames for database persistence

- **TYU5DirectWriter** (`lib/trading/pnl_integration/tyu5_direct_writer.py`)
  - Persists TYU5 results to database
  - Tables: tyu5_trades, tyu5_positions, tyu5_summary, tyu5_risk_matrix, tyu5_position_breakdown

#### Data Flow:
```
Trade Ledger CSVs → TradeLedgerAdapter → TYU5Runner → TYU5DirectWriter → pnl_tracker.db
Market Prices DB changes ↗
```

## Deprecated/Legacy Components

### UnifiedPnLService TradeFileWatcher
- **Status**: NO LONGER USED
- **Reason**: Populated deprecated `cto_trades` table
- **Replaced by**: PNLPipelineWatcher for TYU5 calculations

## Runner Scripts

### Individual Watchers:
1. `scripts/run_market_price_monitor.py` - Market price file monitoring
2. `run_spot_risk_watcher.py` - Spot risk processing
3. `scripts/run_pnl_watcher.py` - TYU5 pipeline watcher

### Unified Service:
- `scripts/run_all_watchers.py` - Starts all three watchers in threads
- `run_all_watchers.bat` - Windows batch file for easy startup

## Database Schema

### market_prices.db
- **market_prices** table:
  - Symbol, Current_Price, Flash_Close, Prior_Close
  - Updated by both MarketPriceFileMonitor and SpotRiskPriceProcessor

### pnl_tracker.db
- **TYU5 tables** (active):
  - tyu5_trades, tyu5_positions, tyu5_summary
  - tyu5_risk_matrix, tyu5_position_breakdown
  - tyu5_runs (metadata)
- **FULLPNL** table (preserved)
- **Legacy tables** (dropped): cto_trades, processed_trades, etc.

## Key Design Decisions

1. **Multiple Price Sources**: Market prices come from both Bloomberg files (2pm/4pm) and spot risk files (real-time theoretical)

2. **Full Reprocessing**: TYU5 pipeline reprocesses ALL trade ledgers on each run for simplicity and consistency

3. **Thread-Based Architecture**: Each watcher runs in its own thread with unified logging and shutdown

4. **Debounce Mechanisms**: 10-second debounce prevents rapid re-triggering of expensive calculations

5. **Direct DataFrame Persistence**: TYU5 results are captured as DataFrames and written directly to SQLite, bypassing intermediate formats

## Monitoring and Debugging

### Logs:
- All watchers use unified logging format
- Log level: INFO by default
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Health Checks:
- Thread monitoring in unified service
- Automatic restart notification if thread dies
- Graceful shutdown on Ctrl+C

### Common Issues:
1. **File locks**: Ensure Excel/other apps aren't locking CSV files
2. **Database locks**: SQLite WAL mode helps with concurrent access
3. **Memory usage**: Monitor for large trade files or accumulation

## Future Considerations

1. **Consolidation**: Consider merging overlapping functionality
2. **Performance**: Add incremental processing for large datasets
3. **Monitoring**: Add metrics/dashboards for pipeline health
4. **Error Recovery**: Implement automatic retry mechanisms 