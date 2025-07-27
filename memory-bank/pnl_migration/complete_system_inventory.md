# Complete System Inventory

## File Watchers Inventory

### 1. TradeFileWatcher
- **Location**: `lib/trading/pnl_calculator/trade_preprocessor.py`
- **Function**: Monitors trade ledger directory for new trade CSV files (`trades_*.csv`). Converted to skeleton with callbacks for new PnL module integration.
- **Type**: Class-based, polling mechanism
- **Status**: Skeleton (PnL logic removed)

### 2. PipelineWatcher  
- **Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py`
- **Function**: Generic file monitoring framework using watchdog library. Can watch multiple directories with different file patterns and callbacks.
- **Type**: Event-driven using watchdog Observer
- **Status**: Skeleton (PnL logic removed)

### 3. MarketPriceFileMonitor
- **Location**: `lib/trading/market_prices/file_monitor.py`
- **Function**: Monitors futures and options directories for CSV price files. Processes files to extract flash close (2pm) and prior close (4pm) prices.
- **Type**: Event-driven using watchdog Observer with MarketPriceFileHandler
- **Status**: Active

### 4. SpotRiskWatcher
- **Location**: `lib/trading/actant/spot_risk/file_watcher.py`
- **Function**: Monitors input directory for spot risk CSV files. Calculates Greeks using bond future option models and updates market prices database.
- **Type**: Event-driven using watchdog Observer with SpotRiskFileHandler
- **Status**: Active

### 5. ActantFileMonitor
- **Location**: `lib/trading/actant/pnl/parser.py`
- **Function**: Monitors directory for latest Actant CSV files (GE_*.csv pattern). Provides utility to find and load most recent files.
- **Type**: Polling-based directory scanner
- **Status**: Active (utility class)

### 6. PriceUpdateTrigger
- **Location**: `lib/trading/market_prices/price_update_trigger.py`
- **Function**: Monitors market_prices.db for changes using threading. Previously triggered TYU5 calculations, now partially broken.
- **Type**: Database monitoring with threading
- **Status**: Partially broken (TYU5 references removed)

### 7. SpotRiskFileHandler
- **Location**: `lib/trading/market_prices/spot_risk_file_handler.py`
- **Function**: Specialized handler for spot risk files when used with market price monitoring. Processes spot risk data into market prices.
- **Type**: Event handler (FileSystemEventHandler)
- **Status**: Active

### 8. FileChangeHandler
- **Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py` (inner class)
- **Function**: Generic file change handler with debouncing for PipelineWatcher. Handles file creation and modification events.
- **Type**: Event handler (FileSystemEventHandler)
- **Status**: Active (part of skeleton)

## Databases Inventory

### 1. spot_risk.db
- **Location**: `data/output/spot_risk/spot_risk.db`
- **Function**: Stores spot risk analysis data including raw inputs, calculated Greeks, and processing sessions
- **Tables**: spot_risk_sessions, spot_risk_raw, spot_risk_calculated
- **Size**: 39MB

### 2. market_prices.db
- **Location**: `data/output/market_prices/market_prices.db`
- **Function**: Central price database storing futures and options prices with flash close (2pm) and prior close (4pm) values
- **Tables**: futures_prices, options_prices
- **Size**: 280KB

### 3. actant_data.db
- **Location**: `data/output/ladder/actant_data.db`
- **Function**: Stores Actant ladder data for scenario analysis dashboard
- **Tables**: ladder_data (presumed)
- **Size**: Unknown

### 4. actant_eod_data.db
- **Location**: `data/output/eod/actant_eod_data.db`
- **Function**: Stores Actant end-of-day data processed from JSON files
- **Tables**: eod_data (presumed)
- **Size**: Unknown

### 5. observatory.db
- **Location**: `apps/dashboards/main/logs/observatory.db`
- **Function**: Primary monitoring database for @monitor decorator, stores function execution logs and metrics
- **Tables**: monitor_records, function_calls, etc.
- **Size**: 36KB

### 6. observability.db
- **Location**: `apps/dashboards/main/logs/observability.db`
- **Function**: Secondary monitoring database, appears to be legacy or duplicate of observatory.db
- **Tables**: Similar to observatory.db
- **Size**: 36KB

### 7. main_dashboard_logs.db
- **Location**: `apps/dashboards/main/logs/main_dashboard_logs.db`
- **Function**: Stores main dashboard specific logs and activity
- **Tables**: dashboard_logs (presumed)
- **Size**: Unknown

### 8. demo_app_simple_logs.db
- **Location**: `apps/demos/logs/demo_app_simple_logs.db`
- **Function**: Demo application logging database
- **Tables**: demo_logs (presumed)
- **Size**: Unknown

### 9. query_timing_logs.db
- **Location**: `apps/demos/logs/query_timing_logs.db`
- **Function**: Stores query performance timing data for demos
- **Tables**: query_timings (presumed)
- **Size**: Unknown

### 10. decorator_test_logs.db
- **Location**: `apps/demos/logs/decorator_test_logs.db`
- **Function**: Test database for decorator functionality
- **Tables**: test_logs (presumed)
- **Size**: Unknown

### 11. query_runner_demo_data.db
- **Location**: `apps/demos/logs/query_runner_demo_data.db`
- **Function**: Demo data for query runner application
- **Tables**: demo_data (presumed)
- **Size**: Unknown

### 12. function_logs.db
- **Location**: `logs/function_logs.db` (default name in handlers.py)
- **Function**: Default SQLite handler database for function logging
- **Tables**: function_logs (presumed)
- **Size**: Unknown

### 13. Test Databases
- **Location**: `data/output/test_*.db` (multiple)
- **Function**: Various test databases for integration testing
- **Examples**: test_intraday_precision.db, test_positions.db, test_positions_real.db, test_sod_eod_precision.db
- **Size**: ~76KB each

## File Watcher Scripts

### 1. run_spot_risk_watcher.py
- **Location**: `scripts/run_spot_risk_watcher.py`
- **Function**: Standalone script to run SpotRiskWatcher. Processes spot risk files and updates databases.
- **Status**: Active

### 2. run_market_price_monitor.py
- **Location**: `scripts/run_market_price_monitor.py`
- **Function**: Standalone script to run MarketPriceFileMonitor for standard input directories.
- **Status**: Active

### 3. run_corrected_market_price_monitor.py
- **Location**: `scripts/run_corrected_market_price_monitor.py`
- **Function**: Alternative market price monitor for Z:\Trade_Control directories with custom handlers.
- **Status**: Active

### 4. run_all_watchers.bat
- **Location**: `run_all_watchers.bat`
- **Function**: Windows batch file attempting to run all watchers. References non-existent run_all_watchers.py.
- **Status**: Broken

## Summary

### Active File Watchers: 7
1. MarketPriceFileMonitor (market prices)
2. SpotRiskWatcher (spot risk analysis)
3. ActantFileMonitor (Actant CSV files)
4. SpotRiskFileHandler (spot risk for market prices)
5. FileChangeHandler (generic handler)
6. PriceUpdateTrigger (partially broken)
7. Various script-based watchers

### Skeleton Watchers: 2
1. TradeFileWatcher (ready for PnL integration)
2. PipelineWatcher (ready for PnL integration)

### Active Databases: 13+
- Core trading: spot_risk.db, market_prices.db, actant_data.db, actant_eod_data.db
- Monitoring: observatory.db, observability.db, main_dashboard_logs.db
- Demo/Test: Various demo and test databases
- Removed: pnl_tracker.db (confirmed deleted) 