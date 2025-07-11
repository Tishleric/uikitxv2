# Code Index

This file provides a quick reference to all code files in the project with brief descriptions.

## Applications

### Main Dashboard (`apps/dashboards/main/`)
- `app.py` - Main dashboard entry point with page routing logic for all sub-dashboards

### Spot Risk Dashboard (`apps/dashboards/spot_risk/`)
- `app.py` - Spot Risk dashboard application entry point
- `controller.py` - Business logic controller (MVC pattern) - handles CSV data loading, Greek calculations, and profile generation. Updated to support daily subfolder structure with `_get_latest_date_folder()` method.
- `views.py` - UI components and layout definitions with Greek display groups
- `callbacks.py` - Dash callbacks for interactivity, Greek graph generation, and filters
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

#### Spot Risk (`lib/trading/actant/spot_risk/`)
- `__init__.py` - Module exports
- `parser.py` - CSV parsing for spot risk data
- `calculator.py` - Greek calculations for spot risk positions
- `aggregator.py` - Position aggregation by underlying
- `file_watcher.py` - Automatic file monitoring and processing. Updated to support daily subfolder structure with 3pm EST boundaries.
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

### Example Scripts
- `examples/spot_risk_watcher_example.py` - Example of using file watcher with daily subfolders

## Data Files

### Input Data
- `data/input/actant_spot_risk/` - Raw spot risk CSV files (now organized in YYYY-MM-DD subfolders)
- `data/input/actant_pnl/` - P&L analysis input files
- `data/input/eod/` - End-of-day data files

### Output Data
- `data/output/spot_risk/` - Processed spot risk files with Greeks (now organized in YYYY-MM-DD subfolders)
- `data/output/eod/` - Processed EOD data
- `data/output/reports/` - Generated reports

### Reference Data
- `data/reference/` - Static reference data files

## Configuration

- `pyproject.toml` - Project configuration and dependencies
- `assets/custom_styles.css` - Custom CSS for dashboards
- `memory-bank/` - Project documentation and memory files
