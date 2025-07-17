# Code Index

Structured registry of all code files in the uikitxv2 project.
Last updated: January 2025

## Core Infrastructure

### lib/trading/
- `symbol_translator.py`: Actant to Bloomberg symbol translation for futures and options
- `treasury_notation_mapper.py`: Comprehensive mapping between Bloomberg, Actant, and CME notation for US Treasury futures and options. Supports all major treasury contracts (TY, TU, FV, US, TN, UB) and weekly options series.

### lib/trading/actant/

### lib/trading/pnl_calculator/storage.py
Database interface for P&L tracking system. Manages trades, positions, market prices, and snapshots. Key methods: save_processed_trades(), save_market_prices(), get_market_price(), get_positions(), create_eod_snapshot(). Includes _map_to_bloomberg() which uses SymbolTranslator for instrument mapping. Updated get_market_price() to use flexible timestamp lookup instead of exact hour matching. **July 17, 2025: Removed all UNIQUE constraints and deduplication logic to allow multiple trades with same trade_id from different days.**

### lib/trading/pnl_calculator/calculator.py
Core P&L calculation engine implementing FIFO methodology. Handles futures and options with different precision (5 decimal for futures, 4 for options). Methods: calculate_pnl_for_trades(), calculate_position_pnl(), calculate_realized_pnl(), calculate_unrealized_pnl(). Processes exercise assignments and manages rounding for display.

### lib/trading/pnl_calculator/trade_preprocessor.py
Processes raw trade CSV files into standardized format. Monitors data/input/trade_ledger/ directory, tracks processing state, and manages transaction types (BUY/SELL/EXERCISE). Integrates with PnLCalculator and PositionManager for real-time updates. **July 17, 2025: Updated to process all trades without duplicate checking, allowing same trade_id from different days.**

### lib/trading/pnl_calculator/service.py
Main service orchestrating P&L tracking components. Manages file watchers, coordinates trade processing, price updates, and position calculations. Methods: start(), stop(), process_pending_files(), get_current_positions(). Implements singleton pattern for global access.

### lib/trading/pnl_calculator/unified_service.py
Higher-level service wrapping PnLService with additional data aggregation. Provides clean API for UI: get_open_positions(), get_trade_history(), get_daily_pnl_history(). Manages component lifecycle and formats data for display.

### lib/trading/pnl_calculator/position_manager.py
Manages real-time position tracking with FIFO methodology. Processes trades, updates positions, calculates P&L, and integrates market prices. Key methods: process_trade(), update_positions(), update_market_prices(). Handles option exercise assignments specially.

### lib/trading/pnl_calculator/closed_position_tracker.py
Tracks closed positions by analyzing trade history from cto_trades table. Calculates cumulative positions day-by-day and identifies when positions go to zero or flip signs. Key methods: calculate_closed_positions_for_date(), update_positions_table_with_closed_quantities(), get_position_history(). Works with the new closed_quantity column in positions table.

### lib/trading/pnl_calculator/price_processor.py
Processes market price CSV files from Bloomberg. Handles futures and options directories separately. Validates and normalizes price data before storage. Integrates with PnLStorage for database operations.

## Dashboard Applications

### apps/dashboards/pnl_v2/
New P&L tracking dashboard with real-time updates. Components:
- app.py: Main layout with 4 tabs (Open Positions, Trade Ledger, Daily P&L, P&L Chart)
- views.py: Individual tab components and data tables
- controller.py: Singleton managing UnifiedPnLService instance
- callbacks.py: Real-time update callbacks on 5-second intervals

### lib/trading/pnl_integration/
New integration package for TYU5 P&L engine (replacing pnl_calculator). Components:
- tyu5_adapter.py: Adapter querying UIKitXv2 data stores and formatting for TYU5 engine
- tyu5_service.py: Service layer managing calculations, monitoring, and output generation
- Direct database to TYU5 path, bypassing old pnl_calculator entirely

### lib/trading/actant/spot_risk/
Spot risk processing pipeline with Greek calculations. Components:
- parser.py: Parse Actant CSV files, extract expiry dates, load vtexp from CSV mapping
- calculator.py: Calculate implied volatility and all Greeks using bond_future_options API
- file_watcher.py: Monitor input directory, process files automatically, maintain state
- database.py: SQLite storage service for raw data and calculated Greeks. Now stores vtexp values in spot_risk_raw table
- time_calculator.py: Loads vtexp values from pre-calculated CSV files (data/input/vtexp/) instead of calculating them
- vtexp_mapper.py: Maps spot risk options to vtexp values by matching expiry dates (simplified approach)
- schema.sql: Database schema including vtexp column for time to expiry storage
- Dual output: CSV files in data/output/spot_risk/processed/ and SQLite at spot_risk.db

## Recent Updates
- Added SQLite storage to spot risk pipeline alongside CSV output
- Database stores raw data, calculated Greeks, and tracks processing sessions
- Schema includes spot_risk_sessions, spot_risk_raw, and spot_risk_calculated tables
- Test script at scripts/test_spot_risk_db.py for verification
- Modified spot risk processing to read pre-calculated vtexp values from CSV files
- Updated lib/trading/actant/spot_risk/time_calculator.py with load_vtexp_for_dataframe()
- Parser now reads vtexp from data/input/vtexp/ directory instead of calculating internally 
- **July 17, 2025: Created scripts/remove_trade_deduplication.py to drop unique constraints from existing databases** 
- **July 17, 2025: Implemented closed position tracking - added closed_quantity column to positions table**
- **July 17, 2025: Created ClosedPositionTracker class to calculate daily closed positions from trade history**
- **July 17, 2025: Migration script scripts/add_closed_quantity_column.py to update existing databases** 