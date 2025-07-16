# P&L Tracking System Complete Map

## Overview
The UIKitXv2 project has three separate P&L tracking systems:
1. **P&L Tracking v1** - Original implementation
2. **P&L Tracking v2** - Clean reimplementation with unified backend
3. **Actant P&L** - Option-specific P&L with Taylor Series approximations

## System Architecture

### 1. Entry Points in app.py

#### Registration (Lines 187-251)
```python
# Three separate P&L systems registered at startup:
1. Actant PnL (lines 187-197)
   - from apps.dashboards.actant_pnl import register_callbacks
   - app._actant_pnl_callbacks_registered = True

2. P&L Tracking v1 (lines 227-239)
   - from apps.dashboards.pnl.callbacks import register_callbacks
   - app._pnl_tracking_callbacks_registered = True

3. P&L Tracking v2 (lines 241-251)
   - from apps.dashboards.pnl_v2.callbacks import register_pnl_v2_callbacks
   - app._pnl_tracking_v2_callbacks_registered = True
```

#### Navigation System (Lines 2837-2839)
```python
sidebar_items = [
    {"id": "nav-actant-pnl", "label": "Actant PnL", "icon": "📉"},
    {"id": "nav-pnl-tracking", "label": "PnL Tracking", "icon": "💹"},
    {"id": "nav-pnl-tracking-v2", "label": "PnL Tracking V2", "icon": "🚀"},
]
```

#### Dynamic Loading (Lines 2927-2973)
```python
# Each P&L system loaded dynamically when navigation clicked
if page_name == "actant-pnl":
    from apps.dashboards.actant_pnl import create_dashboard_content
    
if page_name == "pnl-tracking":
    from apps.dashboards.pnl import create_pnl_content
    
if page_name == "pnl-tracking-v2":
    from apps.dashboards.pnl_v2 import create_pnl_v2_layout
```

## P&L Tracking v2 Architecture (Recommended System)

### Dashboard Components
```
apps/dashboards/pnl_v2/
├── __init__.py          # Exports: create_pnl_v2_layout
├── app.py               # Main layout definition
├── views.py             # Tab components (positions, trades, daily P&L, chart)
├── controller.py        # Singleton controller managing backend
└── callbacks.py         # Real-time update callbacks (5-second intervals)
```

### Core P&L Calculator Library
```
lib/trading/pnl_calculator/
├── __init__.py              # Module exports
├── models.py                # Trade, Lot dataclasses
├── calculator.py            # FIFO P&L calculation engine
├── storage.py               # SQLite database interface
├── position_manager.py      # Real-time position tracking
├── service.py               # Core orchestration service
├── unified_service.py       # High-level UI service wrapper
├── trade_preprocessor.py    # CSV trade file processor
├── price_processor.py       # Market price file processor
├── trade_file_watcher.py    # Real-time trade file monitoring
├── price_watcher.py         # Real-time price file monitoring
├── price_file_selector.py   # Intelligent price file selection
└── data_aggregator.py       # UI data formatting
```

### Data Flow

#### 1. Input Files
```
data/input/
├── trade_ledger/            # Trade CSV files
│   ├── trades_20250712.csv  # Format: trades_YYYYMMDD.csv
│   ├── trades_20250714.csv  # Growing throughout day
│   └── trades_20250715.csv  # Switches at 4pm CDT
│
└── market_prices/           # Price CSV files
    ├── futures/
    │   └── Futures_YYYYMMDD_HHMM.csv
    └── options/
        └── Options_YYYYMMDD_HHMM.csv
```

#### 2. File Watchers
- **TradeFileWatcher**: Monitors trade_ledger/ directory
  - Detects new/modified trade files
  - Special handling for growing daily files
  - 4pm CDT cutover logic
  
- **PriceFileWatcher**: Monitors market_prices/ directories
  - Processes futures and options price files
  - Time-based file selection (3pm/5pm uploads)
  - Handles "#N/A Requesting Data..." values

#### 3. Processing Pipeline

##### Trade Processing Flow:
```
1. TradeFileWatcher detects change
   ↓
2. TradePreprocessor.process_trade_file()
   - Validates CSV format
   - Maps columns to standard format
   - Handles duplicates
   - Exercise assignment handling
   ↓
3. PnLStorage.save_processed_trades()
   - Saves to processed_trades table
   - Uses UNIQUE constraint for deduplication
   ↓
4. PositionManager.process_trade()
   - Updates FIFO positions
   - Calculates realized P&L
   - Updates position quantities
   ↓
5. PnLCalculator (per instrument)
   - FIFO lot tracking
   - Realized/unrealized calculations
   - Daily P&L breakdowns
```

##### Price Processing Flow:
```
1. PriceFileWatcher detects new file
   ↓
2. PriceProcessor.process_price_file()
   - Validates CSV format
   - Filters invalid prices
   - Maps symbols using SymbolTranslator
   ↓
3. PnLStorage.save_market_prices()
   - Saves to market_prices table
   - Indexed by (bloomberg, upload_date, upload_hour)
   ↓
4. PositionManager.update_market_prices()
   - Fetches latest prices
   - Updates unrealized P&L
   - Creates P&L snapshots
```

#### 4. Database Schema
```sql
-- Main tables in pnl_tracker.db:

1. processed_trades
   - trade_id (unique with source_file)
   - instrument_name, trade_date, quantity, price, side
   
2. market_prices
   - bloomberg, asset_type, px_settle, px_last
   - upload_timestamp, upload_date, upload_hour
   
3. positions
   - instrument_name, position_quantity, avg_cost
   - total_realized_pnl, last_market_price
   
4. pnl_snapshots
   - Real-time P&L tracking
   - Position snapshots with market prices
   
5. eod_pnl
   - Daily summary by instrument
   - Opening/closing positions, realized/unrealized P&L
```

#### 5. Symbol Translation
```
SymbolTranslator: Actant → Bloomberg mapping
- Options: XCMEOCADPS20250714N0VY2/110.75 → VBYN25C2 110.750 Comdty
- Futures: XCMEFFDPSX20250919U0ZN → TYU5 Comdty
- Handles weekday occurrence calculation for options
```

#### 6. UI Updates (5-second intervals)
```python
# controller.py manages singleton UnifiedPnLService
controller = PnLDashboardController()

# callbacks.py registers real-time updates:
- update_summary_cards()     # Total/realized/unrealized P&L
- update_positions_content() # Open positions table
- update_trades_table()      # Trade history
- update_daily_pnl_table()   # Daily P&L breakdown
- update_pnl_chart()         # Cumulative P&L chart
```

### Key Features

1. **FIFO Methodology**: First-in-first-out position tracking
2. **Real-time Updates**: 5-second refresh intervals
3. **Multi-asset Support**: Futures and options with different precision
4. **Exercise Handling**: Special logic for option assignments
5. **Time-aware Processing**: Chicago timezone, 4pm cutover
6. **Robust File Watching**: Handles growing files, duplicates
7. **Market Price Selection**: Intelligent 3pm/5pm price selection

### Database Locations
```
data/output/pnl/
├── pnl_tracker.db         # Main production database (1MB)
├── pnl_dashboard.db       # P&L v1 database
└── backups/               # Database backups
```

## P&L Tracking v1 Architecture (Legacy)

### Components
```
apps/dashboards/pnl/
├── __init__.py      # Exports: create_pnl_content
├── app.py           # Layout and controller initialization
└── callbacks.py     # Dashboard callbacks
```

Uses similar backend but different UI implementation.

## Actant P&L Architecture (Options-specific)

### Components
```
apps/dashboards/actant_pnl/
├── __init__.py           # Exports: PnLDashboard, create_dashboard_content
└── pnl_dashboard.py      # Monolithic implementation (1071 lines)
```

Focuses on:
- Taylor Series P&L approximations
- Greek-based P&L attribution
- Option-specific analytics

## Critical Integration Points

1. **app.py Registration**: All callbacks must be registered at startup
2. **Navigation**: Each system has dedicated navigation entry
3. **File Watchers**: Run continuously in background threads
4. **Database Access**: SQLite with proper connection management
5. **Symbol Translation**: Critical for Actant→Bloomberg mapping
6. **Time Handling**: Chicago timezone throughout system

## Performance Monitoring

All major functions decorated with @monitor():
- Execution time tracking
- Memory usage monitoring
- Error tracking
- Stored in observatory.db

## Known Issues and Considerations

1. **Price File Validation**: Need to handle "#N/A Requesting Data..." values
2. **Growing Files**: Trade files grow throughout day, require special handling
3. **Time Cutover**: 4pm CDT switches to next day's file
4. **Symbol Mapping**: Must maintain accurate Actant→Bloomberg mappings
5. **Database Growth**: P&L snapshots can grow large, need retention policy 