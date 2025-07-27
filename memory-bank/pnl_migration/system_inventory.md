# System Inventory Report

## All File Watchers in Codebase

### 1. TradeFileWatcher
- **Location**: `lib/trading/pnl_calculator/trade_preprocessor.py`
- **Function**: Monitors trade ledger directory for new trade CSV files (`trades_*.csv`). Converted to skeleton with callbacks for new PnL module integration.

### 2. PipelineWatcher  
- **Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py`
- **Function**: Generic file monitoring framework using watchdog library. Can watch multiple directories with different file patterns and callbacks.

### 3. MarketPriceFileMonitor
- **Location**: `lib/trading/market_prices/file_monitor.py`
- **Function**: Monitors futures and options directories for CSV price files. Processes files to extract flash close (2pm) and prior close (4pm) prices.

### 4. SpotRiskWatcher
- **Location**: `lib/trading/actant/spot_risk/file_watcher.py`
- **Function**: Monitors input directory for spot risk CSV files. Calculates Greeks using bond future option models and updates market prices database.

### 5. ActantFileMonitor
- **Location**: `lib/trading/actant/pnl/parser.py`
- **Function**: Monitors directory for latest Actant CSV files (GE_*.csv pattern). Provides utility to find and load most recent files.

### 6. PriceUpdateTrigger
- **Location**: `lib/trading/market_prices/price_update_trigger.py`
- **Function**: Monitors market_prices.db for changes using threading. Previously triggered TYU5 calculations, now partially broken.

### 7. SpotRiskFileHandler
- **Location**: `lib/trading/market_prices/spot_risk_file_handler.py`
- **Function**: Specialized handler for spot risk files when used with market price monitoring. Processes spot risk data into market prices.

### 8. FileChangeHandler
- **Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py` (inner class)
- **Function**: Generic file change handler with debouncing for PipelineWatcher. Handles file creation and modification events.

### 9. MarketPriceFileHandler
- **Location**: `lib/trading/market_prices/file_monitor.py` (inner class)
- **Function**: Handles file system events for market price files. Processes futures and options files based on regex patterns.

### 10. SpotRiskFileHandler (in spot_risk module)
- **Location**: `lib/trading/actant/spot_risk/file_watcher.py` (inner class)
- **Function**: Handles file system events for spot risk CSV files. Detects new files and triggers processing.

## All Databases in Codebase

### 1. spot_risk.db
- **Location**: `data/output/spot_risk/spot_risk.db`
- **Function**: Stores spot risk analysis data including raw inputs, calculated Greeks, and processing sessions.

### 2. market_prices.db
- **Location**: `data/output/market_prices/market_prices.db`
- **Function**: Central price database storing futures and options prices with flash close (2pm) and prior close (4pm) values.

### 3. actant_data.db
- **Location**: `data/output/ladder/actant_data.db`
- **Function**: Stores Actant ladder data for scenario analysis dashboard.

### 4. actant_eod_data.db
- **Location**: `data/output/eod/actant_eod_data.db`
- **Function**: Stores Actant end-of-day data processed from JSON files.

### 5. observatory.db
- **Location**: `apps/dashboards/main/logs/observatory.db`
- **Function**: Primary monitoring database for @monitor decorator, stores function execution logs and metrics.

### 6. observability.db
- **Location**: `apps/dashboards/main/logs/observability.db`
- **Function**: Secondary monitoring database, appears to be legacy or duplicate of observatory.db.

### 7. main_dashboard_logs.db
- **Location**: `apps/dashboards/main/logs/main_dashboard_logs.db`
- **Function**: Stores main dashboard specific logs and activity.

### 8. demo_app_simple_logs.db
- **Location**: `apps/demos/logs/demo_app_simple_logs.db`
- **Function**: Demo application logging database.

### 9. query_timing_logs.db
- **Location**: `apps/demos/logs/query_timing_logs.db`
- **Function**: Stores query performance timing data for demos.

### 10. decorator_test_logs.db
- **Location**: `apps/demos/logs/decorator_test_logs.db`
- **Function**: Test database for decorator functionality.

### 11. query_runner_demo_data.db
- **Location**: `apps/demos/logs/query_runner_demo_data.db`
- **Function**: Demo data for query runner application.

### 12. function_logs.db
- **Location**: `logs/function_logs.db` (default location)
- **Function**: Default SQLite handler database for function logging.

### 13. function_exec.db
- **Location**: `logs/function_exec.db` (default in logging config)
- **Function**: Function execution logging database.

### 14. test_intraday_precision.db
- **Location**: `data/output/test_intraday_precision.db`
- **Function**: Test database for intraday precision testing.

### 15. test_positions.db
- **Location**: `data/output/test_positions.db`
- **Function**: Test database for position tracking testing.

### 16. test_positions_real.db
- **Location**: `data/output/test_positions_real.db`
- **Function**: Test database with real position data.

### 17. test_sod_eod_precision.db
- **Location**: `data/output/test_sod_eod_precision.db`
- **Function**: Test database for start-of-day and end-of-day precision testing.

### 18. test_pnl_tracker.db
- **Location**: `data/output/test_settlement_suite/test_pnl_tracker.db`
- **Function**: Test database for settlement suite testing.

### 19. pnl_tracker.db (REMOVED)
- **Location**: `data/output/pnl/pnl_tracker.db` (DELETED)
- **Function**: Was the main PnL tracking database. Completely removed in Phase 3.

## Status Summary

### File Watchers by Status:
- **Active**: 7 (MarketPriceFileMonitor, SpotRiskWatcher, ActantFileMonitor, handlers)
- **Skeleton**: 2 (TradeFileWatcher, PipelineWatcher)
- **Partially Broken**: 1 (PriceUpdateTrigger)

### Databases by Category:
- **Core Trading**: 4 (spot_risk.db, market_prices.db, actant_data.db, actant_eod_data.db)
- **Monitoring/Logging**: 9 (observatory.db, observability.db, various log databases)
- **Test**: 5+ (various test databases)
- **Removed**: 1 (pnl_tracker.db) 