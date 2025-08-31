# Code Index

Structured registry of all code files in the uikitxv2 project.
Last updated: January 2025

## Scripts
### tools/validate_plex_errors.py
Summarizes Plex accuracy validation CSVs. Walks `lib/trading/bond_future_options/data_validation/accuracy_validation/` for folders ending with `Plex`, selects files ending with `_Plex.csv`, and reports total data rows (excluding headers), rows with `|error_2nd_order| > 5`, percentage per folder, and grand totals. Skips malformed `error_2nd_order` values and reports skipped count. Run with `python tools/validate_plex_errors.py`.
### scripts/data_tools/aggregate_yamansmess_outliers.py
Aggregates all CSVs in `lib/trading/bond_future_options/data_validation/yamansmess/` matching `*outliers.csv` into `yamansmess_outliers_aggregated.csv`. Writes header once (deduplicates column headers only), validates identical headers across inputs, preserves input column order, and appends all rows. Adds no extra columns.
### scripts/filter_review_csvs.py
Utility to prune review CSVs by keeping all rows with error == inf, the top 5 rows (error <= 5) by absolute moneyness, and the top 5 rows by greatest finite error. Preserves header and original row order for selected rows; overwrites files in place. Accepts file paths or auto-discovers review CSVs.

### gamma_ladder_standalone/gamma_ladder.py
Direct conversion of the teammate's Jupyter notebook `gamma shop ladder.ipynb` into a Python script. Preserves original logic and paths. Generates a price ladder around current ZN price from TT live CSV, loads latest PricingMonkey CSV for today, selects closest options by target delta per ladder step, and writes a styled HTML table to `Y:\\Gamma Screener\\option_ladder.html`.

### gamma_ladder_standalone/run_gamma_ladder.bat
Windows launcher to run `gamma_ladder.py` by double-click. Looks for Python in PATH and runs `python -X utf8 gamma_ladder.py` from the script directory. Keeps the console open while running.


### scripts/templates/data_quality_watcher_template.py
Standalone, copyable watcher skeleton for data quality monitoring. Mirrors our watcher mechanics (watchdog Observer + FileSystemEventHandler, start/stop lifecycle, graceful shutdown, Windows-safe keepalive loop). No monitoring decorator or external integrations; teammate sets `--watch-dir`, `--pattern`, and fills TODOs in correctness/frequency/completeness checks.

### scripts/migration/001_add_tyu5_tables.py
Database migration script that adds TYU5 P&L system tables. Creates lot_positions, position_greeks, risk_scenarios, match_history, and pnl_attribution tables. Extends positions table with short_quantity and match_history columns. Implements reversible migration with up() and down() methods, tracks status in schema_migrations table.

### scripts/verify_tyu5_schema.py
Verification script that checks if TYU5 schema migration was applied correctly. Validates all new tables exist, indexes are created, positions table has new columns, and WAL mode is enabled. Provides detailed output showing table structures and migration status.

### scripts/run_all_watchers.py
### scripts/run_sod_roll_service.py
Perpetual service that, around 5:00 PM Chicago time, copies the latest trading day’s `close` prices into `pricing.sodTod` with a `YYYY-MM-DD 06:00:00` timestamp, mirroring the trusted behavior in `scripts/rebuild_historical_pnl.py`. Idempotent and publishes a Redis `positions:changed` signal so the positions aggregator refreshes.

Unified watcher service that starts all three file watchers in separate threads. Manages MarketPriceFileMonitor (2pm/4pm price files), SpotRiskWatcher (spot risk + current prices), and PNLPipelineWatcher (TYU5 calculations). Provides unified logging, graceful shutdown, and thread monitoring. Central entry point for all file monitoring.

### scripts/diagnostics/verify_sod_roll.py
Read-only verifier for SOD roll state against a SQLite DB. Prints cwd, resolved DB path, PRAGMA database_list, latest close date, counts of `close` vs `sodTod` on that date, distinct `sodTod` times, and latest `sodTod` date. Exit codes: 0 pass, 2 mismatch, 3 schema/env issue.

### scripts/diagnostics/manual_sod_roll_now.py
Safe manual SOD roll utility. Prefers `sodTom → sodTod` on latest sodTom date (preserves timestamps) and clears `sodTom`; falls back to `close → sodTod` at 06:00 when `sodTom` is absent. Supports dry-run and `--execute`.

### scripts/run_pnl_watcher.py
Runner script for PNLPipelineWatcher service. Monitors trade ledger CSV files and market prices database for changes, triggers full TYU5 P&L calculation pipeline. Processes all trade ledgers (not just most recent), filters zero-price and midnight trades. Updates tyu5_* tables in pnl_tracker.db.

### scripts/run_market_price_monitor.py
Runner script for MarketPriceFileMonitor. Monitors futures and options price directories for CSV files. Processes files based on time windows: 2pm CDT ± 15 min for Current_Price, 4pm CDT ± 15 min for Prior_Close. Updates market_prices table in market_prices.db. Includes callbacks for processing status.

### scripts/indexer/scan_repo.py
Repository scanner that walks the entire tree (excluding `.git`, `__pycache__`, `.pytest_cache`) and emits a JSONL manifest with path, size, mtime, extension, binary flag, and SHA-1. Output written to `memory-bank/index/manifest.jsonl`. Serves as the foundation for comprehensive indexing and coverage checks.

### scripts/indexer/extract_python_ast.py
### scripts/add_pricingmonkey_column.py
Adds a `PricingMonkey` column to `data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv` for option rows (skips futures). The value is a base key without strike/side: "<mon><yy> wkN <dow> ty" (e.g., "sep25 wk1 thu ty"). Week index N is the 1-based occurrence of the weekday in that month, derived from the `Option Expiration Date (CT)` column.
AST extractor for all Python files. Captures module docstrings, imports, top-level functions (names and args), and classes (bases and methods). Outputs JSONL to `memory-bank/index/python_ast.jsonl`. Used to synthesize summaries, import graphs, and API surfaces.

### scripts/translate_bbg_to_actantrisk.py
Utility script that reads a list of Bloomberg symbols (one per line, default `bbgsymbolstotranslate.md`), translates each to ActantRisk using `RosettaStone.translate(symbol, 'bloomberg', 'actantrisk')`, and writes results to CSV at `data/output/symbol_translations/bbg_to_actantrisk.csv`. Allows overriding input/output paths via `--input` and `--output`.

### scripts/run_actant_spot_risk_archiver.py
Perpetual archiver for Spot Risk input data. Mirrors and moves files from `C:\\Users\\ceterisparibus\\Documents\\Next\\uikitxv2\\data\\input\\actant_spot_risk` to `C:\\Users\\ceterisparibus\\Documents\\HistoricalMarketData`, preserving structure. Uses atomic day-folder renames for folders older than today, and hourly sweeps of today’s folder for stable files (≥60 min). Writes append-only CSV ledger and logs under `%PROGRAMDATA%\\ActantArchive`.

### scripts/run_five_minute_market_snapshot.py
Perpetual snapshot service that reads the latest complete 16-chunk Actant Spot Risk batch, computes Greeks for all rows (futures and options), and writes a CSV every five minutes to `C:\\Users\\ceterisparibus\\Documents\\ProductionSpace\\Hanyu\\FiveMinuteMarket\\<trading-day>\\`. Trading day rolls at 5:00 PM Chicago. Uses existing parser and calculator modules; independent from existing watchers.

### configs/five_minute_market.yaml
### scripts/fivemin_market_search.py
Comprehensive scanner for `FiveMinuteMarket` snapshots. Parses CT timestamps from filenames, maps each file to a trading day (session 5pm–4pm CT), computes per-day 5‑minute coverage with gap statistics, reads expiries from CSVs, and evaluates all rolling 5‑business‑day windows for expiry progression. Outputs JSON reports (`coverage_by_day.json`, `candidates.json`) and a manifest-ready mapping of bins to files. Accepts CLI args with sensible defaults.

Configuration file for the Five-Minute Market Snapshot service. Keys include `input_dir`, `output_root`, `interval_minutes`, `timezone`, `vtexp_dir`, `enabled_greeks`, `stale_max_minutes`, and `filename_pattern`.

### pm_standalone/pm_runner.py
Standalone Pricing Monkey automation script. Opens Chrome to `https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c`, performs keyboard navigation (TAB×7, DOWN, Ctrl+Shift+Down, Ctrl+Shift+Right), copies the grid to clipboard, parses into a pandas DataFrame, and saves a CSV named `pmonkey_MMDDYYYY_HH-MM-SS.csv` under `Z:\Hanyu\FiveMinuteMonkey\MM-DD-YYYY\`. Writes a per-run log `pm_run_YYYYMMDD_HH-MM-SS.log` to the working directory.

### pm_standalone/run_pm_standalone.bat
Windows batch launcher for the standalone PM script. Ensures pip and installs required dependencies (`pywinauto`, `pyperclip`, `pandas`) if missing, then runs `pm_runner` every 5 minutes in a perpetual loop. Logs are written by the Python script in the batch's working directory.

### pm_standalone/install_pm_requirements.bat
One-time dependency installer. Detects your Python (Anaconda/Miniconda or system), ensures pip, and installs `pywinauto`, `pyperclip`, and `pandas`. Use this first on a new machine; the run script assumes dependencies are present.

### pm_standalone/run_pm_playwright_diagnostics.bat
Runs a full Playwright viability diagnostic: installs Playwright and Edge support if missing, launches Edge with a dedicated profile, navigates to PM, saves screenshots, attempts DOM text extraction, performs page-scoped (non-OS) keyboard selection and clipboard capture, and writes diagnostic CSV/logs under `pm_standalone/logs/`.

### pm_standalone/pm_playwright_probe.py
Python probe used by the diagnostics batch. Implements the diagnostic steps: Edge launch with persistent profile, PM navigation, screenshots, DOM text dump, page-scoped selection/clipboard capture, and CSV parsing with explicit headers.

### pm_standalone/pm_runner_playwright.py
Persistent Playwright-based runner that launches Edge once with a dedicated profile, prompts for first-run login, polls for data readiness, performs in-tab selection/copy each cycle, parses to CSV with headers, and sleeps (30s dev). Keeps the Edge window open between cycles to preserve login.

### pm_standalone/run_pm_playwright_runner.bat
Minimal launcher for the Playwright runner. Runs `python -X utf8 pm_runner_playwright.py` from the folder and leaves the console open on exit.

### pm_standalone/pm_runner_playwright_1hz.py
High-frequency (1 Hz) stress-test runner. Launches Edge with anti-throttling flags, reuses in-tab key selection, polls readiness, saves CSVs to `pm_standalone/test_output/<date>/`, and logs per-cycle stats to `logs/`.

### pm_standalone/run_pm_playwright_runner_1hz.bat
Launcher for the 1 Hz stress runner.

### lib/trading/pricing_monkey/playwright_basic_runner.py
Playwright Edge one-shot collector for Pricing Monkey. Opens board `cbe072b5-…513d`, sends key sequence (TAB×7, DOWN×3, Ctrl+Shift+Down, Ctrl+Shift+Right), waits for all "Loading..." cells to clear, copies selection via page-scoped clipboard, parses into a pandas DataFrame, and prints shape/head. Uses a dedicated `.edge_profile_basic` and does not persist a loop.

### apps/dashboards/pm_basic/app.py
Minimal Dash app named `pm_scenario`. Uses wrapped components (`Container`, `Button`, `DataTable`). Clicking "Run Pricing Monkey" invokes `PMBasicRunner.collect_once()` and displays the full resulting DataFrame in a themed DataTable, with a status line showing row/column counts. Assets sourced from project `assets/`.

### apps/dashboards/yamansmess_outliers/app.py
Dash app that reads `yamansmess_outliers_aggregated.csv` and renders six scatter plots with |error| on Y: `del_f`, `del_c`, `del_t`, `del_iv`, `vtexp`, and `moneyness` on X. Loads CSV at startup, coerces numeric types, and displays graphs in a two-per-row layout. Run with `python apps/dashboards/yamansmess_outliers/app.py`.

## Tests

### tests/trading/test_tyu5_schema_migration.py
Comprehensive test suite for TYU5 schema migration. Tests migration up/down operations, verifies all tables and indexes are created, checks schema compatibility with existing data, and ensures migration is idempotent. Uses temporary databases for isolated testing.

### tests/test_spot_risk_parsing_pipeline.py
Comprehensive unit test suite for spot risk CSV parsing pipeline. Tests file detection, CSV parsing, symbol translation, future price extraction, VTEXP mapping, and parameter assembly for Greek calculations. Uses actual CSV data from production format. Key findings: symbol translation working (e.g., XCME.ZN.SEP25 -> TYU5 Comdty, XCME.WY1.06AUG25.110.C -> TYWQ25C1 110 Comdty), VTEXP mapping successful for all options, all parameters correctly assembled for Greek API calls.

### tests/diagnostics/price_updater_diagnostic.py
Comprehensive diagnostic tool for price updater latency issues. Simulates spot risk pipeline with detailed timing breakdown for each operation: pickle deserialization, Arrow deserialization, price extraction, symbol translation, and database updates. Includes SpotRiskSimulator to generate test data and PriceUpdaterDiagnostic for timing analysis. Provides summary statistics to identify bottlenecks.

### tests/diagnostics/monitor_price_pipeline.py
Real-time pipeline monitor that observes Redis pub/sub traffic without interference. Tracks message latency, payload sizes, and processing rates. Calculates statistics including average/max latency and message throughput. Also includes DatabaseMonitor to check for lock contention. Non-intrusive tool for production monitoring.

### tests/diagnostics/test_database_bottleneck.py
Focused database performance testing tool. Tests single update timing, batch vs individual commits, WAL mode configuration, concurrent writer performance, and file system I/O speeds. Provides optimization suggestions based on findings. Designed to identify if database operations are causing the observed 14-second per message latency.

## Documentation

### docs/tyu5_migration_deep_analysis.md
### docs/bond_future_options_analytics_guide.md
Orientation guide for the bond future options analytics package. Summarizes each file’s role (API, facade, factory, model, core engine, analytical formulas), explains how the `ModelFactory` selects models, and provides a math-first review path to verify Greek accuracy. Aimed at math-proficient readers new to the code.

Comprehensive deep system analysis comparing TYU5 P&L system with TradePreprocessor pipeline. Covers architecture comparison, data models, calculation methodologies, and proposes 4-phase hybrid integration strategy. Key findings: TYU5 has advanced FIFO with short support and Bachelier option pricing, while TradePreprocessor offers production reliability and SQLite integration. Recommends preserving both systems' strengths through incremental migration.

## Core Infrastructure

### core/
- `archiver_protocol.py`: Protocol specifying the minimal interface for long-running archiver services (`run_once` and `run_forever`). Enables consistent orchestration and testing across different archiver implementations.

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
### apps/dashboards/aggregated_explorer/
- `app.py`: Small internal Dash app to explore aggregated option CSVs. Lets user pick weekday (Mon–Thu codes plus Friday `OZN_SEP25`), side (C/P), start and end timestamps (deduped from target CSV), and displays two tables for the selected rows.
- `service.py`: Filesystem-backed data service implementing `AggregatedDataService` for listing days/sides, reading unique timestamps, and fetching rows by exact timestamp. Handles Friday exception naming `aggregated_OZN_SEP25_[C|P].csv`.

### core/
- `aggregated_data_protocol.py`: ABC specifying `AggregatedDataService` interface for day/side listing, timestamp enumeration, and row retrieval by timestamp. Used by the Aggregated Explorer app.
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

### tests/trading/pnl_fifo_lifo/
- **test_sod_roll.py** - Unit tests for the SOD roll utility. Verifies that latest `close` prices are copied to `sodTod` with the expected timestamp and that the operation is idempotent on repeated runs.
- **test_trade_insertions.py** - Comprehensive unit tests for trade database insertions in FIFO/LIFO system. Tests correct insertion into trades_fifo, trades_lifo, realized_fifo, and realized_lifo tables. Verifies no duplicate entries, proper FIFO vs LIFO ordering, partial/full offsets, P&L calculations, and transaction atomicity. Includes test for positions aggregator query using master symbol list approach.
- **test_end_to_end_flow.py** - End-to-end integration test simulating complete flow from trade entry to dashboard display. Tests trade processing, positions aggregation, and dashboard queries. Verifies open/closed positions calculation directly from trades and realized tables.

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

### run_verify_sod_roll.bat
Runs the SOD roll verification script against `trades.db` and paginates the output.

### run_manual_sod_roll_now.bat
Interactive helper to perform a safe manual SOD roll: runs a dry run first; on confirmation, creates a timestamped backup of `trades.db` and executes the roll.

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

- **`positions_aggregator.py`**: The `PositionsAggregator` class. Runs as a persistent service, subscribing to the `spot_risk:results_channel` on Redis. Consumes Greek data and combines with trade data to update the master `positions` table. Uses master symbol list approach to pull open positions from trades_fifo and closed positions directly from realized_fifo/lifo tables, avoiding dependency on daily_positions table.

#### Spot Risk Pipeline (`lib/trading/actant/spot_risk/`)
- **`file_watcher.py`**: Contains the `SpotRiskWatcher` (the "Producer"). Manages file watching, the parallel worker pool for calculations, and publishes results to the Redis channel.
- **`database.py`**: `SpotRiskDatabaseService` for all interactions with the `spot_risk.db` SQLite database (now primarily for logging and historical session tracking).
- **`parser.py`**: Logic for parsing the raw `bav_analysis_*.csv` files into a clean pandas DataFrame.
- **`calculator.py`**: `SpotRiskGreekCalculator` which takes a DataFrame and calculates all required Greeks using the `bond_future_options` library. Now includes `_convert_itype_to_instrument_type()` method and adds `instrument_type` column to output DataFrame for proper instrument classification in the positions table. Supports contract-specific DV01 values for futures (ZN: 64.2, US: 140, FV: 42, TU: 22.7) and configurable Greek calculations via GreekConfiguration.
- **`greek_config.py`**: Greek configuration module that allows selective calculation of Greeks for performance optimization. Default enabled: delta, gamma, speed, theta in F and Y space. Supports environment variable override via SPOT_RISK_GREEKS_ENABLED.
- **`time_calculator.py`**: Utilities for calculating `vtexp` (time to expiry) for options, using pre-calculated values from `data/input/vtexp/`. 