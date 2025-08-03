# Code Index

Structured registry of all code files in the uikitxv2 project.
Last updated: January 2025

## Scripts

### scripts/migration/001_add_tyu5_tables.py
Database migration script that adds TYU5 P&L system tables. Creates lot_positions, position_greeks, risk_scenarios, match_history, and pnl_attribution tables. Extends positions table with short_quantity and match_history columns. Implements reversible migration with up() and down() methods, tracks status in schema_migrations table.

### scripts/verify_tyu5_schema.py
Verification script that checks if TYU5 schema migration was applied correctly. Validates all new tables exist, indexes are created, positions table has new columns, and WAL mode is enabled. Provides detailed output showing table structures and migration status.

### scripts/run_all_watchers.py
Unified watcher service that starts all three file watchers in separate threads. Manages MarketPriceFileMonitor (2pm/4pm price files), SpotRiskWatcher (spot risk + current prices), and PNLPipelineWatcher (TYU5 calculations). Provides unified logging, graceful shutdown, and thread monitoring. Central entry point for all file monitoring.

### scripts/run_pnl_watcher.py
Runner script for PNLPipelineWatcher service. Monitors trade ledger CSV files and market prices database for changes, triggers full TYU5 P&L calculation pipeline. Processes all trade ledgers (not just most recent), filters zero-price and midnight trades. Updates tyu5_* tables in pnl_tracker.db.

### scripts/run_market_price_monitor.py
Runner script for MarketPriceFileMonitor. Monitors futures and options price directories for CSV files. Processes files based on time windows: 2pm CDT ± 15 min for Current_Price, 4pm CDT ± 15 min for Prior_Close. Updates market_prices table in market_prices.db. Includes callbacks for processing status.

## Tests

### tests/trading/test_tyu5_schema_migration.py
Comprehensive test suite for TYU5 schema migration. Tests migration up/down operations, verifies all tables and indexes are created, checks schema compatibility with existing data, and ensures migration is idempotent. Uses temporary databases for isolated testing.

## Documentation

### docs/tyu5_migration_deep_analysis.md
Comprehensive deep system analysis comparing TYU5 P&L system with TradePreprocessor pipeline. Covers architecture comparison, data models, calculation methodologies, and proposes 4-phase hybrid integration strategy. Key findings: TYU5 has advanced FIFO with short support and Bachelier option pricing, while TradePreprocessor offers production reliability and SQLite integration. Recommends preserving both systems' strengths through incremental migration.

## Core Infrastructure

### lib/trading/
- `symbol_translator.py`: Actant to Bloomberg symbol translation for futures and options
- `treasury_notation_mapper.py`: Comprehensive mapping between Bloomberg, Actant, and CME notation for US Treasury futures and options. Supports all major treasury contracts (TY, TU, FV, US, TN, UB) and weekly options series.

### lib/trading/fullpnl/
Core package for automating FULLPNL master P&L table builds. Replaces 10+ manual scripts with unified framework.
- `__init__.py`: Package initialization exposing main classes: FULLPNLBuilder, SymbolMapper
- `symbol_mapper.py`: Centralized symbol format conversion between Bloomberg, Actant, and vtexp formats. Handles futures, options with all strike notations and contract mappings
- `data_sources.py`: Database adapter classes for accessing P&L tracker, spot risk, and market prices SQLite databases. Provides unified interface for data retrieval
- `builder.py`: Main orchestrator class that rebuilds FULLPNL table. Implements column loaders for positions, market prices, spot risk data, and Greeks. Supports both full rebuild and incremental updates

### lib/trading/pnl_integration/
- `trade_ledger_adapter.py`: Direct adapter for reading trade ledger CSV files and transforming to TYU5 format. Features: parses XCME symbols (futures/options), generates both TYU5 and Bloomberg symbols, filters zero-price expiry trades, includes midnight trades, and pre-fetches market prices directly from database using Bloomberg symbols to bypass TYU5Adapter translation issues.
- `pnl_pipeline_watcher.py`: File watcher service for automated TYU5 pipeline execution. Contains PNLPipelineHandler for trade ledger monitoring, MarketPriceMonitor for database polling. Implements 10-second debounce mechanism, tracks processed files, triggers full pipeline on changes. Central automation for TYU5 P&L calculations.

### lib/trading/market_prices/
- `file_monitor.py`: Core market price file monitoring service with MarketPriceFileMonitor class. Watches futures/options directories for new CSV files, processes based on CDT time windows (2pm/4pm). MarketPriceFileHandler validates filenames, determines processing window, and routes to appropriate processors. Integrates with watchdog for file system events.

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

## Scripts

### scripts/test_fullpnl_automation.py
Comprehensive test script for FULLPNL automation components. Tests symbol mapping, database connections, and builder functionality. Verifies all 7 unit tests pass.

### scripts/test_fullpnl_rebuild.py
Full rebuild test script for FULLPNLBuilder. Tests complete rebuild process, displays table contents, coverage statistics, and performance metrics. Also tests incremental update mode.

### scripts/check_fullpnl_table.py
Quick status check script for FULLPNL table. Displays summary statistics, coverage percentages, and sample data rows for verification.

## Tests

### tests/fullpnl/test_symbol_mapper.py
Unit tests for SymbolMapper class. Tests all symbol format conversions including Bloomberg, Actant, vtexp formats. Covers futures, options, various strike notations, and edge cases.

## Dashboard Applications

### apps/dashboards/pnl_v2/
New P&L tracking dashboard with real-time updates. Components:
- app.py: Main layout with 4 tabs (Open Positions, Trade Ledger, Daily P&L, P&L Chart)
- views.py: Individual tab components and data tables
- controller.py: Singleton managing UnifiedPnLService instance
- callbacks.py: Real-time update callbacks on 5-second intervals

### lib/trading/pnl_integration/
- **unified_pnl_api.py** - Unified P&L API that merges TradePreprocessor and TYU5 data. Provides comprehensive queries for positions with lots, Greeks, risk scenarios, P&L attribution, and match history. Central interface for accessing all advanced P&L features.

### lib/trading/pnl_calculator/
- **unified_service.py** - Enhanced unified service now with TYU5 integration. Provides methods for lot-level positions, portfolio Greeks, risk scenarios, and comprehensive position views. Falls back gracefully when TYU5 features unavailable.

### tests/trading/
- **test_unified_service_enhanced.py** - Comprehensive test suite for enhanced UnifiedPnLService. Tests TYU5 feature integration including lot tracking, Greeks, risk scenarios, and fallback behavior. Includes direct API tests.

### scripts/
- **test_unified_service_enhanced.py** - Demonstration script showing Phase 3 unified service capabilities. Examples of accessing lot details, Greeks, risk scenarios, and comprehensive position views through the unified API.

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

### lib/trading/pnl_integration/tyu5_database_writer.py
Database writer for TYU5 P&L calculation results. Persists lot positions, Greeks, risk scenarios and match history to SQLite. Handles vtexp loading from latest CSV, 32nds price format conversion, bulk inserts for performance, and full transaction management with rollback. Fixed to map symbols back to Bloomberg format for position_id lookup.

### tests/trading/test_tyu5_database_writer.py
Comprehensive test suite for TYU5DatabaseWriter. Tests lot position writing, Greek value persistence, risk scenario storage, match history tracking, vtexp loading, and transaction rollback on errors. Validates all data transformations and database operations.

### scripts/test_tyu5_db_integration.py  
Integration test script for TYU5 database persistence. Runs full TYU5 calculation via TYU5Service and verifies results are properly stored in database tables. Tests end-to-end flow from trade processing to database persistence.

### scripts/debug_tyu5_writer.py
Debug helper for TYU5 database writer. Reads TYU5 Excel output and attempts to write to database with detailed logging. Shows structure of Excel sheets and identifies any data transformation issues.

### scripts/check_tyu5_db_results.py
Verification script for TYU5 database persistence. Queries database tables to show counts and sample data for lot positions and risk scenarios. Confirms successful Phase 2 implementation.

### apps/dashboards/pnl/callbacks.py

### lib/trading/market_prices/spot_risk_price_processor.py
Extracts current prices from Actant spot risk CSV files to populate Current_Price column in market prices database. Uses ADJTHEOR when available, falls back to BID/ASK midpoint. Integrates with SpotRiskSymbolTranslator for Actant to Bloomberg symbol mapping. Automatically triggered when new spot risk files are processed.

### scripts/add_current_price_column.py
Migration script to add Current_Price column to futures_prices and options_prices tables. Allows market prices database to store theoretical/mid prices from spot risk files alongside Flash_Close and prior_close from Bloomberg feeds.

### scripts/test_spot_risk_price_update.py
Test script for verifying spot risk price updates. Processes a spot risk CSV file, updates Current_Price in market prices database, and displays results including futures and options price counts.

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
- `lib/trading/pnl/tyu5_pnl/core/breakdown_generator.py` - Generates lot-level position breakdown. Fixed to handle symbol format mismatch when looking up positions.
- **July 18, 2025: Added Current_Price column to market prices database, populated from spot risk ADJTHEOR values**
- **July 18, 2025: Created SpotRiskPriceProcessor to extract prices from spot risk files with symbol translation**
- **July 18, 2025: Integrated price updates into SpotRiskFileHandler for automatic Current_Price updates**

## Batch Files

### run_all_watchers.bat
Windows batch file for unified watcher service. Checks for Anaconda Python installation, installs required dependencies (watchdog, pytz, pandas, numpy), and launches scripts/run_all_watchers.py. Provides user-friendly interface for starting all file monitoring services on Windows.

### run_spot_risk_watcher.bat
Windows batch file for Spot Risk Watcher service. Validates Anaconda Python path, ensures watchdog is installed, and runs the spot risk file monitoring service. Monitors data/input/actant_spot_risk/ for new files. 

## TYU5 P&L Components

### `lib/trading/pnl/tyu5_pnl/core/position_calculator.py`
Core TYU5 component for position and P&L calculation. Contains two classes, PositionCalculator2 (older, not actively used by main.py) and PositionCalculator (active). Calculates positions from trades, tracks realized/unrealized P&L, handles price updates, and runs attribution analysis for options. Preserves full symbol with strike information (e.g., "ZN3N5 P 110.25") instead of truncating. Fixed symbol variable overwriting in attribution logic. Added Flash_Close column to positions output for complete price transparency. 

`eod_snapshot_service.py` - Service that monitors for 4pm settlement price updates and calculates end-of-day P&L snapshots with settlement-aware logic. Leverages TYU5's existing FIFO logic and writes daily snapshots to tyu5_eod_pnl_history table.

`market_price_monitor.py` - Monitors market_prices.db for 4pm settlement price batch completion. Tracks which symbols have received updates and determines when sufficient coverage (95% default) has been achieved to trigger EOD calculations.

`settlement_constants.py` - Defines Chicago timezone constants and utilities for CME settlement times (2pm settlement, 4pm EOD). Provides functions to calculate settlement boundaries and split positions at 2pm for settlement-aware P&L calculations.

`pnl_pipeline_watcher.py` - Monitors trade ledger CSV files and market prices database for changes, triggering TYU5 P&L calculations with a 10-second debounce. Integrates with the TYU5 pipeline for automated P&L updates.

`tyu5_service.py` - Main TYU5 calculation service that runs FIFO-based P&L calculations. Reads trades from database, applies market prices, and generates position breakdowns with realized/unrealized P&L. Outputs to Excel or CSV and persists to tyu5_ tables.

`tyu5_database_writer.py` - Persists TYU5 calculation results to database tables including tyu5_trades, tyu5_positions, tyu5_summary, tyu5_risk_matrix, and tyu5_position_breakdown. Maintains FIFO lot tracking for accurate P&L attribution.

`trade_preprocessor.py` - Preprocesses raw trade data from CSV files, enriching with instrument metadata and standardizing formats. Handles both futures and options trades with proper symbol mapping and timestamp preservation.

`trade_ledger_adapter.py` - Adapts raw trade ledger CSV data into standardized format for TYU5 processing. Maps column names, handles data types, and ensures trade timestamps are preserved for settlement boundary calculations.

`tyu5_runner.py` - Lower-level runner that executes TYU5 calculations by orchestrating trade loading, position tracking, and P&L computation. Implements FIFO logic for position management and handles both futures and options.

## scripts/

`run_eod_monitor.py` - Standalone script or service component that monitors for 4pm price updates and triggers EOD P&L snapshots. Supports manual calculation mode and configurable monitoring windows (default 3pm-6pm Chicago time).

`test_eod_phase1.py` - Phase 1 verification script that tests EOD history table creation, settlement time calculations, and basic EOD service initialization. Validates that settlement boundaries work correctly for P&L splitting.

`test_eod_phase2.py` - Phase 2 verification script that tests market price monitoring, TYU5 integration, manual EOD calculation, and history views. Confirms the complete EOD pipeline is functioning with FIFO logic.

## scripts/migration/

`002_add_eod_history_table.py` - Database migration that creates tyu5_eod_pnl_history table for storing daily P&L snapshots with settlement-aware calculations. Includes views for daily totals and latest snapshots with proper indexes.

## apps/dashboards/pnl_v2/

`app.py` - Main P&L V2 dashboard entry point that creates the Dash application with TYU5-based real-time P&L display. Shows positions, P&L metrics, and integrates with the live calculation pipeline. 

## Trading Libraries

### lib/trading/pnl_fifo_lifo/
- `__init__.py` - Main module exports for FIFO/LIFO P&L calculation system
- `config.py` - Configuration constants for P&L calculations including database names, table names, and trading methods
- `pnl_engine.py` - Core calculation logic for FIFO/LIFO trade processing, realized/unrealized P&L calculations, and historical pricing support
- `data_manager.py` - Database operations, CSV loading, pricing management, and data queries for the P&L system
- `main.py` - Command-line interface and orchestration for P&L calculations with support for single/multi CSV processing and reporting
- `test_simulation.py` - Test simulation that replicates notebook calculations to verify module accuracy

### lib/trading/pnl_integration/ [DEPRECATED]
- `pnl_pipeline_watcher.py` - Minimal file watcher skeleton (DEPRECATED - use lib/trading/pnl_fifo_lifo instead)
- `DEPRECATED.md` - Deprecation notice directing to new FIFO/LIFO module 

### Standalone Services & Core Logic

- **`positions_aggregator.py`**: The `PositionsAggregator` class. Runs as a persistent service, subscribing to the `spot_risk:results_channel` on Redis. It consumes complete Greek data packages and combines them with trade data to update the master `positions` table in `trades.db`. This is the central point of integration for P&L.

#### Spot Risk Pipeline (`lib/trading/actant/spot_risk/`)
- **`file_watcher.py`**: Contains the `SpotRiskWatcher` (the "Producer"). Manages file watching, the parallel worker pool for calculations, and publishes results to the Redis channel.
- **`database.py`**: `SpotRiskDatabaseService` for all interactions with the `spot_risk.db` SQLite database (now primarily for logging and historical session tracking).
- **`parser.py`**: Logic for parsing the raw `bav_analysis_*.csv` files into a clean pandas DataFrame.
- **`calculator.py`**: `SpotRiskGreekCalculator` which takes a DataFrame and calculates all required Greeks using the `bond_future_options` library. Now includes `_convert_itype_to_instrument_type()` method and adds `instrument_type` column to output DataFrame for proper instrument classification in the positions table.
- **`time_calculator.py`**: Utilities for calculating `vtexp` (time to expiry) for options, using pre-calculated values from `data/input/vtexp/`. 