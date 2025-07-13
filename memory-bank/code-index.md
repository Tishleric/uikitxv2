# Code Index

This file provides a quick reference to all code files in the project with brief descriptions.

## Applications

### Main Dashboard (`apps/dashboards/main/`)
- `app.py` - Main dashboard entry point with page routing logic for all sub-dashboards. Now includes both Actant PnL (original Taylor Series comparison) and PnL Tracking (new FIFO system) as separate tabs.

### Spot Risk Dashboard (`apps/dashboards/spot_risk/`)
- `app.py` - Spot Risk dashboard application entry point
- `controller.py` - Business logic controller (MVC pattern) - handles CSV data loading, Greek calculations, and profile generation. Updated to support daily subfolder structure with `_get_latest_date_folder()` method. Added `_transform_greeks_to_y_space()` method that properly transforms F-space Greeks to Y-space with 1000x scaling when Y-space is selected. Fixed Y-space transformation for cached profiles by applying the same transformation logic in the cached profile processing path. Added `_adjust_greeks_for_put()` method to apply put-call parity adjustments (delta_put = delta_call - 1) for put options, ensuring negative delta values are displayed correctly. Contains debug logging to trace both Y-space transformation and put adjustment flows.
- `views.py` - UI components and layout definitions with Greek display groups. Added file completion stores and file watcher interval for automatic refresh on processing completion. Added model parameters display section showing Future Price, DV01, Convexity, and Average Implied Volatility values. File watcher interval set to 5 seconds to prevent UI flickering while maintaining responsiveness.
- `callbacks.py` - Dash callbacks for interactivity, Greek graph generation, and filters. New `check_file_completion` callback monitors file watcher state and triggers automatic refresh when processing completes. Added `update_model_parameters` callback to display Future Price, DV01 (63.0), Convexity (0.0042), and average Implied Volatility per expiry (displayed as decimal, e.g., 0.7550).
- `state.py` - State management for Greek selections and UI preferences

### Observatory Dashboard (`apps/dashboards/observatory/`)
- `app.py` - Observatory dashboard for monitoring decorated functions
- `callbacks.py` - Real-time data updates and filtering callbacks
- `layout.py` - Dashboard layout with monitoring components
- `state.py` - State management for filters and data
- `views.py` - View components for logs, metrics, and visualizations

### Actant Dashboards
- `actant_eod/app.py` - End-of-day processing dashboard
- `actant_pnl/pnl_dashboard.py` - P&L analysis dashboard with Greeks
- `actant_preprocessing/app.py` - Data preprocessing dashboard

### P&L Tracking Dashboard (`apps/dashboards/pnl/`) - Ready for future integration as separate tab
- `__init__.py` - Module exports for create_pnl_content
- `app.py` - P&L tracking dashboard layout with tabs for positions, daily summaries, charts, and trade history
- `callbacks.py` - Real-time update callbacks with 20-second refresh interval and manual refresh

### Ladder Dashboard (`apps/dashboards/ladder/`)
- `scenario_ladder.py` - Scenario ladder with live/demo toggle
- `zn_price_tracker.py` - Real-time ZN price tracking

## Libraries

### Components (`lib/components/`)
- `core/base_component.py` - Abstract base class for all UI components
- `core/protocols.py` - Protocol definitions for component interfaces
- `basic/` - Button, Container, Toggle, ComboBox, RadioButton, etc.
- `advanced/` - DataTable, Graph, Loading components
- `factory/component_factory.py` - Factory for creating themed components
- `themes/colour_palette.py` - Color theme definitions

### Monitoring (`lib/monitoring/`)
- `decorators/monitor.py` - @monitor decorator for function tracking
- `decorators/context_vars.py` - Context variable management
- `decorators/trace_closer.py` - Trace closure detection
- `writers/sqlite_writer.py` - SQLite backend for monitoring data
- `queues/observatory_queue.py` - Queue for monitoring events
- `retention/manager.py` - Data retention policy management
- `circuit_breaker.py` - Circuit breaker pattern implementation

### Trading Libraries

#### P&L Calculator (`lib/trading/pnl_calculator/`)
- `__init__.py` - Module exports for Trade, Lot, PnLCalculator, Storage, Watcher, Service, and Controller
- `models.py` - Trade and Lot dataclasses with validation
- `calculator.py` - Main FIFO P&L calculator with realized/unrealized P&L tracking, position management, and daily P&L breakdowns. Includes CSV loading from trade ledger format.
- `storage.py` - SQLite storage layer for market prices, trades, P&L snapshots, and EOD summaries. Implements time-based price selection logic (3pm/5pm EST rules).
- `watcher.py` - Watchdog-based file monitoring for trade and market price CSV files with debouncing and startup processing.
- `service.py` - Central orchestration service managing calculator, storage, and file watching. Handles immediate P&L calculation on trade updates and automatic EOD at 5pm EST.
- `controller.py` - Dashboard controller providing thin wrapper around service for UI data transformation. Formats P&L as dollar amounts with red/green coloring.

#### Spot Risk (`lib/trading/actant/spot_risk/`)
- `__init__.py` - Module exports
- `parser.py` - CSV parsing for spot risk data
- `calculator.py` - Greek calculations for spot risk positions
- `aggregator.py` - Position aggregation by underlying
- `file_watcher.py` - Automatic file monitoring and processing. Updated to support daily subfolder structure with 3pm EST boundaries. Features persistent state tracking via JSON file to avoid reprocessing files on restart.
- `interfaces.py` - Type definitions and interfaces
- `processor.py` - Main processing orchestrator

#### Bond Future Options (`lib/trading/bond_future_options/`)
- `bachelier_greek.py` - Bachelier model Greek calculations with Taylor series
- `constants.py` - Model constants and configuration
- `formula_reference.py` - Mathematical formula documentation
- `greeks_calculator.py` - High-level Greek calculation interface
- `models/option_model.py` - Option data models
- `models/types.py` - Type definitions

#### Actant EOD/SOD Processing
- `actant/eod/processor.py` - End-of-day data processing
- `actant/sod/processor.py` - Start-of-day data processing
- `actant/pnl/calculator.py` - P&L calculations

#### TT API Integration (`lib/trading/tt_api/`)
- `config.py` - API configuration settings
- `token_manager.py` - OAuth token management
- `utils.py` - API utility functions

## Tests

### Unit Tests
- `tests/components/` - UI component rendering tests
- `tests/monitoring/` - Monitoring and decorator tests
- `tests/trading/pnl_calculator/test_calculator.py` - Comprehensive tests for FIFO P&L calculations, short positions, and position summaries
- `tests/actant_spot_risk/` - Spot risk calculation tests, including new `test_file_watcher_subfolders.py`
- `tests/bond_future_options/` - Greek calculation tests

### Integration Tests
- `tests/integration/test_basic_integration.py` - Cross-module tests
- `tests/dashboard/test_dashboard_callbacks.py` - Dashboard interaction tests

## Scripts

### Utility Scripts
- `scripts/actant_pnl_formula_extractor.py` - Extract formulas from Excel
- `scripts/migration/fix_component_imports.py` - Fix import statements
- `scripts/spot_risk_migrate_to_daily_folders.py` - Migrate existing files to daily folder structure
- `scripts/validate_decorators.py` - Validate @monitor usage
- `data/input/market_prices/generate_mock_prices.py` - Generate mock market price data with XCME format matching trade CSV structure

### Example Scripts
- `examples/spot_risk_watcher_example.py` - Example of using file watcher with daily subfolders

## Data Files

### Input Data
- `data/input/actant_spot_risk/` - Raw spot risk CSV files (now organized in YYYY-MM-DD subfolders)
- `data/input/actant_pnl/` - P&L analysis input files
- `data/input/eod/` - End-of-day data files
- `data/input/trade_ledger/` - Daily trade CSV files (trades_YYYYMMDD.csv format)
- `data/input/market_prices/` - Market price CSV files for 3pm and 5pm uploads

### Output Data
- `data/output/spot_risk/` - Processed spot risk files with Greeks (now organized in YYYY-MM-DD subfolders)
- `data/output/eod/` - Processed EOD data
- `data/output/reports/` - Generated reports
- `data/output/pnl/` - P&L tracking database and snapshots

### Reference Data
- `data/reference/` - Static reference data files

## Configuration

- `pyproject.toml` - Project configuration and dependencies
- `assets/custom_styles.css` - Custom CSS for dashboards
- `memory-bank/` - Project documentation and memory files
