# Active Context & Next Steps

**Current Focus**: Unified Watcher Service Implementation
**Task**: Created unified script to run all file watchers  
**Status**: ✅ COMPLETE (July 21, 2025)

## Active Pipelines and Watchers (CURRENT STATE)

### 1. Market Price File Monitor (`MarketPriceFileMonitor`)
- **Script**: `scripts/run_market_price_monitor.py`
- **Purpose**: Monitor and process market price CSV files
- **Monitors**: 
  - `data/input/market_prices/futures/`
  - `data/input/market_prices/options/`
- **Processing Windows**:
  - 2:00 PM CDT ± 15 minutes → Updates Current_Price
  - 4:00 PM CDT ± 15 minutes → Sets next day's Prior_Close
- **Output**: Updates `market_prices` table in `data/output/market_prices/market_prices.db`

### 2. Spot Risk Watcher (`SpotRiskWatcher`)
- **Script**: `run_spot_risk_watcher.py`
- **Purpose**: Process spot risk files AND update current market prices
- **Monitors**: `data/input/actant_spot_risk/`
- **Dual Functionality**:
  1. Processes spot risk Greek calculations → `data/output/spot_risk/`
  2. Updates market prices via `SpotRiskPriceProcessor` → `market_prices.db`
- **Price Source**: Uses ADJTHEOR value or (BID+ASK)/2 as fallback

### 3. PNL Pipeline Watcher (`PNLPipelineWatcher`)
- **Script**: `scripts/run_pnl_watcher.py`
- **Purpose**: Monitor for changes and trigger TYU5 P&L calculations
- **Monitors**:
  - Trade ledger files: `data/input/trade_ledger/trades_*.csv`
  - Market prices DB: `data/output/market_prices/market_prices.db`
- **Processing**: 
  - Reads ALL trade ledger CSVs (not just most recent)
  - Filters out zero-price and midnight trades
  - Runs full TYU5 pipeline on any change
- **Output**: Populates `tyu5_*` tables in `data/output/pnl/pnl_tracker.db`

### 4. Unified Watcher Service (NEW)
- **Script**: `scripts/run_all_watchers.py`
- **Batch File**: `run_all_watchers.bat`
- **Purpose**: Start all three watchers in separate threads
- **Benefits**:
  - Single command to start all watchers
  - Unified logging
  - Graceful shutdown handling
  - Thread monitoring for reliability

## Data Flow Architecture
```
Market Price CSVs (2pm/4pm) → MarketPriceFileMonitor → market_prices.db
Spot Risk CSVs → SpotRiskWatcher → market_prices.db + spot risk output
Trade Ledger CSVs + market_prices.db → PNLPipelineWatcher → TYU5 tables
```

## Important Notes
- **NO LONGER USED**: `UnifiedPnLService`'s `TradeFileWatcher` (populated deprecated `cto_trades` table)
- **All watchers can run independently** or via unified service
- **Market prices populated from TWO sources**: regular price files AND spot risk files

## Key Achievements (July 21, 2025)
- Created unified watcher service (`run_all_watchers.py`)
- Created Windows batch file for easy startup
- Verified all watchers work independently
- Eliminated duplicate trade file processing
- Clear separation of concerns between watchers

## Previous Context (July 20, 2025)
- Created TradeLedgerAdapter that bypasses legacy database completely
- Implemented PNLPipelineWatcher for automated TYU5 processing
- Successfully integrated with TYU5 P&L calculation engine
- Added processing of ALL trade ledgers (not just most recent)

## Previous Achievements (July 18, 2025)
- Added Current_Price column to futures_prices and options_prices tables  
- Created SpotRiskPriceProcessor to extract ADJTHEOR/BID-ASK midpoint
- Integrated with existing SpotRiskFileHandler for automatic updates
- Successfully tested with 57 prices (1 future, 56 options) updated

## Files Created/Updated (July 21)
- `scripts/run_all_watchers.py` - Unified watcher service
- `run_all_watchers.bat` - Windows batch file for easy startup
- `memory-bank/activeContext.md` - Updated documentation
- `memory-bank/code-index.md` - Will update next 