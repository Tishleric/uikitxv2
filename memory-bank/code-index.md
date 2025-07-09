# Code Index

## Component Factory (NEW)
- `lib/components/factory/__init__.py` - Factory module exports, provides DashComponentFactory class
- `lib/components/factory/component_factory.py` - Main factory class that creates components with sensible defaults, supports theme injection and config overrides
- `lib/components/factory/defaults.py` - Default configurations for all component types (data=[], page_size=10, etc.)
- `lib/components/factory/templates.py` - Template methods for common patterns like datatable_in_grid, form_grid, dashboard_layout

## Overview
This index provides a quick reference to all code files in the UIKitXv2 project, organized by the new package structure.

## Package Structure

### lib/ (Main Package Directory)
The core UIKitXv2 package, installable via `pip install -e .`

#### lib/__init__.py
Main package initializer that exposes submodules for convenient imports. Contains critical module aliasing that allows `from components import Button` syntax to work throughout the project.

A comprehensive summary of each code file with its purpose and key functionality in the reorganized project structure.

## Library Code (`lib/`)

### Components (`lib/components/`)

#### Basic Components (`lib/components/basic/`)
- **button.py** - Button wrapper for dbc.Button with theme support and styled interactions
- **checkbox.py** - Checkbox wrapper for dcc.Checklist with themed styling and multi-select support
- **combobox.py** - ComboBox wrapper for dcc.Dropdown with theme support, search, and option management
- **container.py** - Container wrapper for dbc.Container providing themed layout containers
- **listbox.py** - ListBox wrapper for dcc.Dropdown in multi-select mode for option selection
- **loading.py** - Loading wrapper for dcc.Loading providing theme-consistent loading indicators
- **radiobutton.py** - RadioButton wrapper for dcc.RadioItems providing single-choice selection
- **rangeslider.py** - RangeSlider wrapper for dcc.RangeSlider with automatic mark generation
- **tabs.py** - Tabs wrapper for dbc.Tabs providing themed tab interfaces
- **toggle.py** - Toggle wrapper for daq.ToggleSwitch with flexible label positioning
- **tooltip.py** - Tooltip wrapper for dbc.Tooltip providing hover tooltips with HTML content support

#### Advanced Components (`lib/components/advanced/`)
- **datatable.py** - DataTable wrapper for dash_table.DataTable with pagination and filtering
- **graph.py** - Graph wrapper for dcc.Graph with theme-integrated plotly figures
- **grid.py** - Grid wrapper for dbc.Row/dbc.Col providing responsive layout system
- **mermaid.py** - Mermaid diagram component wrapper supporting themed diagram rendering

#### Core (`lib/components/core/`)
- **base_component.py** - Abstract base class for all UI components, ensures ID and theme handling
- **protocols.py** - Protocol definitions including MermaidProtocol and DataServiceProtocol

#### Themes (`lib/components/themes/`)
- **colour_palette.py** - Theme dataclass, default_theme, and component styling functions

### Monitoring (`lib/monitoring/`)

#### Decorators (`lib/monitoring/decorators/`)
- **monitor.py** - Complete @monitor decorator integrating observability pipeline. Features automatic queue integration, SmartSerializer for argument/result capture, exception traceback preservation, singleton pattern for global queue/writer, sampling rate support (0.0-1.0), process group categorization, enhanced output naming (handles None, tuples, custom objects, dicts, Dash components with IDs), and minimal performance overhead (<50µs). Main entry point for function monitoring. Fixed async generator exception handling (June 17, 2025). Enhanced output naming for Dash components (January 6, 2025).
- **context_vars.py** - Shared context variables for tracing and logging decorators
- **trace_time.py** - Decorator for logging function execution time and storing in context
- **trace_closer.py** - Decorator for managing resource tracing and flow trace logs
- **trace_cpu.py** - Decorator for measuring CPU usage delta during execution
- **trace_memory.py** - Decorator for measuring RSS memory usage delta
- **EXECUTIVE_SUMMARY.md** - Comprehensive overview of the observability system, architecture, features, file locations, migration guide from legacy decorators, and quick start examples. Production-ready documentation for teams adopting the system.

#### Process Groups (`lib/monitoring/`)
- **process_groups.py** - Intelligent process group assignment strategies. Includes:
  - ModuleBasedStrategy: Groups by module hierarchy (configurable depth)
  - PatternBasedStrategy: Regex matching on function names
  - SemanticStrategy: Analyzes function names and docstrings for I/O, compute, API operations
  - LayeredStrategy: Groups by architectural layers (presentation, business, data, infrastructure)
  - CompositeStrategy: Combines multiple strategies with priorities
  - ProcessGroupStrategies: Pre-configured strategies for microservices, data pipelines, trading systems
  - auto_monitor decorator: Automatic group assignment without manual specification

#### Logging (`lib/monitoring/logging/`)
- **config.py** - Logging configuration with console and SQLite handlers setup (@monitor applied to setup_logging, shutdown_logging)
- **handlers.py** - SQLiteHandler processing FLOW_TRACE logs into database tables

#### Serializers (`lib/monitoring/serializers/`)
- **smart.py** - SmartSerializer class for converting Python objects to string representations. Handles all data types including primitives, collections, NumPy arrays, Pandas DataFrames, custom objects, and circular references. Features include sensitive field masking, configurable truncation, and intelligent representation of complex data structures. Core component of the observability system for capturing function arguments and return values.

#### Queues (`lib/monitoring/queues/`)
- **observatory_queue.py** - ObservatoryQueue with error-first strategy and zero-loss guarantees. Features dual queue system (unlimited error queue + 10k normal queue), overflow ring buffer (50k capacity), automatic recovery mechanism, comprehensive metrics tracking, thread-safe operations, and rate-limited warnings. Core component ensuring errors are never dropped while managing normal record overflow gracefully.

#### Writers (`lib/monitoring/writers/`)
- **sqlite_writer.py** - Production-ready SQLite writer with BatchWriter thread for observability data persistence. Features include continuous queue draining at configurable intervals, batch inserts with transaction management, WAL mode for concurrent access, comprehensive database statistics tracking, graceful shutdown with final flush, automatic schema creation, and JSON conversion for lazy-serialized objects. Achieves 1500+ records/second sustained write throughput while maintaining data integrity.

#### Performance (`lib/monitoring/performance/`)
- **__init__.py** - Performance module exports: FastSerializer, MetadataCache, get_metadata_cache
- **fast_serializer.py** - Optimized serializer with fast paths for common data types. Features include direct passthrough for primitives (str, int, float, bool, None), lazy serialization for large objects (>10k chars or >1k items), efficient handling of simple collections, fallback to SmartSerializer for complex cases. Achieves < 5µs overhead for common types.
- **metadata_cache.py** - LRU cache for function metadata and frequently used values. Features include configurable size (default 10k entries) and TTL (default 1 hour), thread-safe operations, automatic eviction of stale entries, caching of module/qualname lookups and source file paths. Reduces repeated metadata calculations.

#### Monitoring Tests & Demos (`tests/monitoring/observability/`)
- **test_observatory_db.py** - Tests for Observatory database separation (5 tests verifying database path changes)
- **test_observatory_models.py** - Tests for Observatory data models (9 tests for data service, metrics aggregator, trace analyzer)
- **test_observatory_views.py** - Tests for Observatory UI views (9 tests for component rendering and tab creation)
- **test_observatory_integration.py** - Integration tests for Observatory dashboard (5 tests for app creation, callbacks, data flow, and error handling)
- **demo_parent_child.py** - Demonstrates parent-child relationship tracking with nested function calls. Shows how thread_id, call_depth, and microsecond timestamps enable reconstruction of call hierarchies. Includes SQL queries for call tree visualization and exclusive/inclusive timing analysis.
- **demo_legacy_migration.py** - Demo showing migration from legacy decorators to unified @monitor with "track everything" approach
- **demo_process_groups.py** - Demo illustrating process groups for organizing monitored functions - shows auto-derivation, business logic grouping, criticality-based grouping, and service-based grouping
- **demo_intelligent_process_groups.py** - Advanced demo of intelligent process group assignment strategies including pattern-based, semantic, and composite approaches
- **test_monitor_comprehensive.py** - Comprehensive test suite for enhanced @monitor decorator with 19 tests covering process groups, CPU/memory tracking, edge cases, sampling rates, and async patterns
- **test_monitor_edge_cases.py** - Edge case and stress tests covering concurrency, memory pressure, exotic function types, async edge cases, error recovery paths, and generator scenarios
- **test_monitor_advanced.py** - Tests for advanced monitor features: async functions, generators, class methods (15 tests)
- **stress_test_concurrency.py** - Comprehensive concurrency stress testing framework with 6 test scenarios: high-frequency calls (20k ops), mixed sync/async, queue contention, error handling under load, memory allocation patterns, and async generator concurrency. Identified SQLite writer as performance bottleneck.
- **test_async_generator_investigation.py** - Deep dive investigation into async generator exception behavior that uncovered double-recording bug
- **test_async_generator_deep_dive.py** - Further investigation into async generator wrapper behavior and Python async internals

#### Resource Monitoring (`lib/monitoring/`)
- **resource_monitor.py** - Resource monitoring abstraction layer providing clean decoupling from psutil. Includes ResourceMonitorProtocol defining the monitoring interface, PsutilMonitor (psutil backend with lazy initialization and graceful error handling), NullMonitor (graceful degradation when monitoring unavailable), MockMonitor (for testing with configurable values and call counting), and global singleton management with get/set_resource_monitor functions. Handles CPU and memory tracking with runtime feature detection and clean separation of concerns.

#### Circuit Breaker (`lib/monitoring/`)
- **circuit_breaker.py** - Simple circuit breaker implementation for preventing cascading failures. Supports three states (CLOSED, OPEN, HALF_OPEN), configurable failure thresholds, timeout periods, and recovery criteria. Thread-safe with comprehensive statistics tracking.

#### Retention Management (`lib/monitoring/retention/`)
- **__init__.py** - Package initialization for retention management system. Exports RetentionManager and RetentionController.
- **manager.py** - Simple, robust retention management for observability data. Implements 6-hour rolling window deletion strategy using basic SQL DELETE operations. Uses WAL mode for better concurrency. No VACUUM operations to avoid spikes in 24/7 trading environments.
- **controller.py** - Controller for orchestrating retention operations. Runs background thread that calls RetentionManager every 60 seconds. Handles errors gracefully with exponential backoff. Provides statistics and monitoring capabilities. Thread-safe with graceful shutdown.

### Trading (`lib/trading/`)

#### Common Utilities (`lib/trading/common/`)
- **price_parser.py** - Price parsing and formatting utilities for treasury/bond trading:
  - `decimal_to_tt_bond_format()` - Convert decimal to TT bond format
  - `tt_bond_format_to_decimal()` - Parse TT format to decimal
  - `parse_treasury_price()` - Parse various treasury price formats
  - `format_treasury_price()` - Format decimal as treasury string
  - `parse_and_convert_pm_price()` - Parse PricingMonkey prices
  - `format_shock_value_for_display()` - Format shock values by type
  - `convert_percentage_to_decimal()` - Convert percentage to decimal

- **date_utils.py** - Trading calendar and date utilities:
  - `get_monthly_expiry_code()` - Get futures month letter codes
  - `get_third_friday()` - Calculate third Friday expiry dates
  - `get_futures_expiry_date()` - Get expiry dates by contract type
  - `parse_expiry_date()` - Parse various date formats
  - `get_trading_days_between()` - Count trading days
  - `is_trading_day()` - Check if date is trading day

#### Actant Integration (`lib/trading/actant/`)

##### EOD (`lib/trading/actant/eod/`)
- **data_service.py** - ActantDataService implementation:
  - Loads and processes JSON data into SQLite
  - Applies risk metric transformations (DV01-based)
  - Provides filtered data access with range support
  - Metric categorization and prefix filtering
  - Pricing Monkey data integration support

- **file_manager.py** - File management utilities:
  - `get_most_recent_json_file()` - Find latest JSON in data directory
  - `get_json_file_metadata()` - Extract file metadata
  - JSON validation and discovery functions

##### SOD (`lib/trading/actant/sod/`)
- **__init__.py** - Exports SOD processing functions like get_underlying, process_trades, actant_main
- **actant.py** - Core SOD processing logic for parsing trade descriptions and generating Actant format
- **pricing_monkey_adapter.py** - Adapter for converting Pricing Monkey formats to Actant formats
- **browser_automation.py** - Browser automation for retrieving data from Pricing Monkey
- **futures_utils.py** - Utilities for futures contract date calculations and expiry handling

##### Spot Risk (`lib/trading/actant/spot_risk/`)
- **__init__.py** - Package initialization with exports for parser and time calculator functions
- **parser.py** - CSV parser for Actant spot risk data (bav_analysis files):
  - `extract_datetime_from_filename()` - Extract datetime from bav_analysis_YYYYMMDD_HHMMSS.csv format
  - `parse_expiry_from_key()` - Parse expiry dates from instrument keys (futures and options)
  - `parse_spot_risk_csv()` - Main parser that normalizes columns, converts numeric data, calculates midpoint prices, extracts expiry dates, sorts by instrument type, and optionally calculates time to expiry
- **time_calculator.py** - Time to expiry calculator using bachelier business day logic:
  - `parse_series_from_key()` - Extract series code (VY, WY, ZN) from instrument key
  - `parse_expiry_date_full()` - Parse expiry date string to datetime
  - `build_expiry_datetime()` - Build full expiry datetime with CME conventions (VY/WY: 14:00, ZN: 16:30)
  - `calculate_vtexp_for_dataframe()` - Calculate time to expiry in years for all options using CSV timestamp

#### Pricing Monkey (`lib/trading/pricing_monkey/`)

##### Automation (`lib/trading/pricing_monkey/automation/`)
- **pm_auto.py** - Multi-option workflow automation using openpyxl:
  - `run_pm_automation()` - Main entry point for automated Excel/browser workflow
  - Manages Excel setup for multiple options with phases
  - Automates browser operations for data paste and retrieval
  - Processes 11-column result sets from Pricing Monkey
  - Writes formatted results back to Excel with percentage formatting

##### Retrieval (`lib/trading/pricing_monkey/retrieval/`)
- **retrieval.py** - Extended browser automation for ActantEOD:
  - `get_extended_pm_data()` - Retrieve 9-column dataset via automation
  - `PMRetrievalError` - Custom exception for retrieval errors
  - Captures risk metrics: DV01 Gamma, Vega, %Delta, Theta
  - Clipboard processing and data validation

- **simple_retrieval.py** - Simple data retrieval with SOD formatting:
  - `get_simple_data()` - Basic 5-column data retrieval
  - `PMSimpleRetrievalError` - Custom exception for simple retrieval
  - `transform_df_to_sod_format()` - Convert PM data to SOD CSV format
  - Handles futures/options contract identification
  - Date-based asset code determination for options

##### Processors (`lib/trading/pricing_monkey/processors/`)
- **processor.py** - PM data processing utilities:
  - `process_pm_for_separate_table()` - Transform PM data for storage
  - `validate_pm_data()` - Validate PM data structure
  - Column standardization and type conversion

- **movement.py** - Market movement data collection and analysis:
  - `get_market_movement_data_df()` - Dashboard-ready data retrieval
  - `get_market_movement_data()` - Raw market movement data collection
  - `SCENARIOS` - Scenario configuration dictionary (base, -4bp, -8bp, etc.)
  - Treasury price parsing and adjustment utilities
  - Splits data by expiry and underlying values

#### Ladder (`lib/trading/ladder/`)
- **__init__.py** - Exports price formatting and SQLite utilities for ladder applications
- **price_formatter.py** - Treasury bond price formatting between decimal and TT special formats
- **csv_to_sqlite.py** - Utilities for converting CSV files to SQLite tables for efficient querying

#### TT API (`lib/trading/tt_api/`)
- **config.py** - Configuration for TT REST API credentials and settings
- **token_manager.py** - TTTokenManager for authentication:
  - Token acquisition, storage, and auto-refresh
  - Multi-environment support (UAT, SIM, LIVE)
  - Request ID generation

- **utils.py** - TT API utility functions:
  - `generate_guid()` - Create new GUID for requests
  - `create_request_id()` - Format TT-compliant request IDs
  - `sanitize_request_id_part()` - Clean request ID components
  - `format_bearer_token()` - Format authorization tokens
  - `is_valid_guid()` - Validate GUID format

#### Actant PnL (`lib/trading/actant/pnl/`)
- **__init__.py** - Main module exports for PnL analysis: OptionGreeks, TaylorSeriesPricer, PnLCalculator
- **calculations.py** - Core PnL calculation engine:
  - `OptionGreeks` - Data class for option parameters and Greeks (delta, gamma, vega, theta)
  - `TaylorSeriesPricer` - Taylor Series approximation for option pricing from neighboring positions
  - `PnLCalculator` - Calculate PnL using Actant vs Taylor Series methods
  - `parse_actant_csv_to_greeks()` - Parse Actant CSV data into OptionGreeks objects
  - Shock multiplier conversion (1 shock = 16 basis points)
- **parser.py** - CSV file parsing utilities:
  - `ActantCSVParser` - Parse Actant-formatted CSV files with greek columns
  - `ActantFileMonitor` - Monitor directories for latest CSV files
  - `load_latest_data()` - Load most recent CSV and return formatted DataFrame
  - Automatic expiration detection and Greek extraction
- **formatter.py** - Data formatting utilities:
  - `PnLDataFormatter` - Format PnL data for display in tables and graphs
  - `format_price()` - Format option prices with appropriate precision
  - `format_pnl()` - Format PnL values with color coding for gains/losses

#### Bond Future Options (`lib/trading/bond_future_options/`)
- **README.md** - Comprehensive documentation with function listings, line numbers, and usage examples. Designed for self-contained sharing of the bond analytics package.

- **requirements.txt** - Minimal Python dependencies (numpy, pandas, scipy, matplotlib)

- **example_usage.py** - Complete examples demonstrating current dashboard pattern and future API pattern with verification

- **__init__.py** - Exports BondFutureOption class, analysis functions, and convenience API

- **api.py** - Clean API for future use (not yet integrated in dashboard):
  - `calculate_implied_volatility()` - User-friendly vol calculation (lines 28-87)
  - `calculate_greeks()` - Simple Greek calculation interface (lines 90-143)
  - `calculate_taylor_pnl()` - Taylor P&L predictions (lines 146-209)
  - `quick_analysis()` - All-in-one analysis function (lines 212-283)
  - `process_option_batch()` - Batch processing for multiple options (lines 286-359)

- **pricing_engine.py** - Core bond future option pricing engine (CTO-validated):
  - `BondFutureOption` - Main class for Bachelier model pricing (lines 15-322)
  - Price/yield volatility conversions
  - Comprehensive Greeks through 3rd order:
    - 1st: delta_F/delta_y, vega_price/vega_y, theta_F
    - 2nd: gamma_F/gamma_y, volga, vanna, charm
    - 3rd: speed, color, ultima, zomma

- **analysis.py** - High-level analysis functions used by dashboard:
  - `solve_implied_volatility()` - Robust implied vol solver (lines 11-59)
  - `calculate_all_greeks()` - Calculate complete Greek set scaled by 1000 (lines 61-111)
  - `analyze_bond_future_option_greeks()` - Main dashboard function (lines 113-178)

- **bachelier_greek.py** - Greek profile and Taylor error analysis (used by dashboard):
  - `bachelier_price()` - Basic Bachelier formula (lines 12-14)
  - `analytical_greeks()` - Analytical Greek calculations (lines 17-50)
  - `numerical_greeks()` - Finite difference Greeks (lines 53-103)
  - `taylor_expand()` - Taylor series expansion (lines 132-144)
  - `generate_greek_profiles_data()` - Dashboard function for Greek curves (lines 200-241)
  - `generate_taylor_error_data()` - Dashboard function for Taylor accuracy (lines 244-305)

- **numerical_greeks.py** - Numerical Greek calculations using finite differences:
  - `compute_derivatives()` - Core finite difference engine for up to 3rd order derivatives
  - `compute_derivatives_bond_future()` - Bond future wrapper with proper scaling
  - `format_greek_comparison()` - Format Greeks for side-by-side comparison table

- **greek_validator.py** - Greek-based PnL prediction validator:
  - `GreekPnLValidator` - Tests how well analytical Greeks predict actual price changes
  - Validates Greek predictive power: R²=0.74 (first-order), R²=0.90 (second-order)

- **demo_profiles.py** - Demonstration code for Greek profile visualization

- **bachelier.py** - Time to expiry calculation utilities (moved from root directory):
  - `minutes_until_expiry_excluding_cme_holidays()` - Calculate business minutes to expiry excluding CME holidays
  - `time_to_expiry_years()` - Calculate exact time to expiry in years from evaluation datetime (business year fraction)
  - `OptionBachelier` - Bachelier model option pricing class
  - `calculate_implied_volatility()` - Calculate implied vol using Bachelier model
  - Supports custom evaluation datetime for historical analysis

- **output/** - Directory for generated outputs (CSV, PNG files)

## Standalone Tools (`SumoMachine/`)

### Pricing Monkey Automation (`SumoMachine/`)
- **__init__.py** - Empty init file for SumoMachine module
- **PmToExcel.py** - Standalone Pricing Monkey to Excel automation:
  - Automated browser navigation to extract data from Pricing Monkey
  - Keyboard automation using pywinauto (tab 8x, down 1x, shift+down 11x, shift+right 4x)
  - Clipboard data parsing for 4-column format (Notes, Trade Description, DV01, DV01 Gamma)
  - Data transformations: comma removal, futures price conversion (32nds), DV01 scaling (/1000)
  - Direct Excel writing to ActantBackend.xlsx using openpyxl
  - Comprehensive logging with timestamp-based log files
  - No dependencies on main project code - fully standalone

## Applications (`apps/`)

### Dashboards (`apps/dashboards/`)

#### ActantEOD Dashboard (`apps/dashboards/actant_eod/`)
- **app.py** - Main ActantEOD dashboard application with real-time market data visualization, P&L metrics, shock scenarios, and scenario-by-metric views. Uses DataServiceProtocol for data abstraction and has complex Dash callbacks for interactive filtering.
- **__init__.py** - Empty init file for ActantEOD dashboard package.

#### ActantSOD Dashboard (`apps/dashboards/actant_sod/`)
- **actant_sod.py** - Placeholder for ActantSOD dashboard

#### Ladder Dashboard (`apps/dashboards/ladder/`)
- **scenario_ladder.py** - Scenario ladder dashboard for price ladder visualization with TT API integration
- **zn_price_tracker.py** - ZN price tracking application

#### Main Dashboard (`apps/dashboards/main/`)
- **app.py** - Main dashboard Dash application with sidebar navigation for Option Hedging, Option Comparison, Greek Analysis (ALL 11 Greeks with summary panel), Scenario Ladder, Actant EOD, Actant PnL, Observatory👀, Project Documentation, and Logs (Legacy). Includes callbacks for all tabs and integrates multiple dashboards including the new Observatory system.
  - Greek Analysis page: Removed original 11 individual Greek graphs, kept Greek profile visualization with all 12 Greeks
  - Added `acp_generate_table_view` callback for dynamic table generation when in table view mode
  - Implements full table/graph toggle for Greek profiles and Taylor approximation error analysis
  - Legend positioning: Moved legends to be inline with titles (above graph area, right-aligned)
  - **Monitor Migration (January 6, 2025)**: Migrated all 30 callbacks and 6 utility functions from legacy decorators (@TraceCloser, @TraceTime, @TraceCpu, @TraceMemory) to single @monitor() decorator for simplified observability
  - **Taylor Error Update (January 7, 2025)**: Converted Taylor approximation error display from absolute values to basis points of underlying futures price (abs_error / future_price × 10000) for both graph and table views
  - **Greek Analysis Inputs (January 9, 2025)**: Updated Market Price input to accept decimal values (0-1) instead of 64ths, and Time to Expiry to accept years (0-1) instead of days
  - **Numerical Methods Removal (January 9, 2025)**: Commented out all numerical (finite difference) calculations and displays from Greek Analysis page, keeping only analytical (Bachelier model) results

#### Actant Preprocessing Dashboard (`apps/dashboards/actant_preprocessing/`)
- **__init__.py** - Package initialization for BFO Greek Analysis dashboard
- **app.py** - Bond Future Options Greek Analysis dashboard:
  - Interactive Greek profile visualization (Delta, Gamma, Vega, Theta)
  - 2x2 grid layout using Plotly Graph components
  - Graph/Table view toggle functionality
  - Parameter input controls for option analysis
  - Real-time Greek recalculation based on user inputs
  - Integration with validated BFO pricing engine

#### Demo Dashboard (`apps/demos/`)
- **app.py** - UIKitXv2 components demo application showcasing tabs, graphs, and data tables
- **test_decorators.py** - Test script demonstrating all decorator combinations
- **flow.py** - Flow control demo application
- **query_runner.py** - Database query execution utility
- **run_queries_demo.py** - Demo script for running database queries
- **queries.yaml** - YAML configuration for demo queries

#### Actant PnL Dashboard (`apps/dashboards/actant_pnl/`)
- **__init__.py** - Module exports: PnLDashboard, create_dashboard_content, register_callbacks
- **pnl_dashboard.py** - Interactive dashboard for option PnL analysis:
  - Side-by-side price and PnL comparison graphs
  - Toggle between Call/Put options and Graph/Table views
  - Real-time Taylor Series approximation calculations
  - Automatic expiration selection from available CSV data
  - Professional dark theme UI with conditional formatting
  - Integration functions for main dashboard sidebar

#### Observatory (`apps/dashboards/observatory/`)
- **views.py** - Observatory dashboard UI with data, exception tables including Duration column (execution time in ms)
- **callbacks.py** - Dash callbacks for refreshing tables, filter persistence, and child process display
- **models.py** - ObservatoryDataService for querying SQLite observatory.db, includes duration_ms formatting
- **constants.py** - Configuration constants for Observatory
- **app.py** - Standalone entry point for Observatory dashboard

## Remaining Original Locations

### TTRestAPI Directory
- **examples/** - Various TT API usage examples
- Response JSON files for reference
- Token files and other configurations

## Entry Points
- **run_actant_eod.py** - Entry point for ActantEOD dashboard (port 8050)
- **run_actant_sod.py** - Entry point for ActantSOD processing
- **run_scenario_ladder.py** - Entry point for Scenario Ladder dashboard (port 8051)
- **run_observatory.py** - Entry point for Observatory dashboard (port 8052)
- **pyproject.toml** - Package configuration with dependencies
- **requirements.txt** - Exact version dependencies for all Python packages used in production and development

## Tests Directory Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_imports.py          # Verify all imports work
├── components/              # Component tests
├── monitoring/              # Decorator and logging tests
│   ├── test_resource_monitor.py  # Tests for resource monitoring abstraction (21 tests)
├── trading/                 # Trading utility tests
├── actant_spot_risk/        # Spot risk parser tests
│   ├── __init__.py
│   ├── test_parser.py       # Comprehensive tests for parser module (18 tests)
│   └── test_real_csv.py     # Test script for real CSV file verification
└── integration/             # Dashboard integration tests
```

## Scripts (`scripts/`)
- **actant_eod/process_actant_json.py** - Processes Actant JSON output into flattened CSV and SQLite format
- **actant_eod/data_integrity_check.py** - Comprehensive data integrity verification for ActantEOD pipeline
- **actant_eod/verify_th_pnl.py** - Simple verification script for Th PnL data integrity
- **actant_sod/pricing_monkey_to_actant.py** - Integration script that retrieves PM data and processes through actant logic
- **actant_pnl_formula_extractor.py** - Extract Excel formulas from actantpnl.xlsx for analysis
- **run_actant_pnl_demo.py** - Run the Actant PnL dashboard in standalone mode for testing
- **bond_options_csv_example.py** - Example script for processing option data from CSV using simplified API

## Data Structure (`data/`)
```
data/
├── input/
│   ├── eod/              # ActantEOD input files
│   ├── sod/              # ActantSOD input files  
│   ├── ladder/           # Ladder input files
│   ├── actant_pnl/       # Actant PnL CSV files (e.g., GE_XCME.ZN_*.csv)
│   ├── actant_spot_risk/ # Spot risk CSV files (bav_analysis_*.csv)
│   └── reference/        # Reference data (actant.csv, SampleZNSOD.csv)
│       └── actant_pnl/   # Reference Excel files (actantpnl.xlsx)
└── output/
    ├── eod/              # ActantEOD outputs (databases)
    ├── sod/              # ActantSOD outputs
    ├── ladder/           # Ladder outputs
    └── reports/          # Generated reports
```

## Backup Structure
- **_backup_old_structure/** - Contains original src/, ActantEOD, and TTRestAPI files
- **_backup_transition_20250531_192926/** - Complete backup before final transition
- **BACKUP_MANIFEST.md** - Documentation of backed up files and restoration instructions

## Core Abstractions (`lib/components/core/`)
- `base_component.py`: Abstract base class defining the component interface. All UI components must inherit from BaseComponent and implement the render() method.
- `__init__.py`: Re-exports BaseComponent for easier imports.

## UI Components (`lib/components/`)

### Basic Components (`lib/components/basic/`)
- `button.py`: Button component wrapping dbc.Button with consistent styling and optional loading states.
- `card.py`: Card component for content containers with headers and customizable styling.
- `datatable.py`: Enhanced DataTable component with sorting, filtering, and pagination capabilities.
- `dropdown.py`: Dropdown selection component with search and multi-select support.
- `graph.py`: Graph component wrapping dcc.Graph with responsive sizing and theming.
- `indicator.py`: KPI indicator component showing metrics with optional comparison values.
- `input.py`: Text input component with validation and error states.
- `slider.py`: Range slider component for numeric inputs.
- `__init__.py`: Re-exports all basic components.

### Advanced Components (`lib/components/advanced/`)
- `grid.py`: Responsive grid layout component using dbc.Row and dbc.Col for flexible layouts.
- `__init__.py`: Re-exports Grid component.

### Theme Management (`lib/components/themes/`)
- `theme_manager.py`: Centralized theme configuration for consistent styling across all components.

### Component Initialization
- `__init__.py`: Main package entry point that re-exports all components for convenient importing.

## Monitoring & Decorators (`lib/monitoring/`)

### Decorators (`lib/monitoring/decorators/`)
- `context_vars.py`: Defines context variables (log_uuid_var, current_log_data) for sharing data between decorator layers.
- `trace_closer.py`: TraceCloser decorator that acts as the outermost wrapper, managing database connections and aggregating trace data.
- `trace_cpu.py`: TraceCpu decorator for monitoring CPU usage during function execution.
- `trace_memory.py`: TraceMemory decorator for tracking memory allocation and usage.
- `trace_time.py`: TraceTime decorator for measuring function execution time.
- `__init__.py`: Re-exports all decorators and context variables.

### Logging Infrastructure (`lib/monitoring/logging/`)
- `lumberjack_config.py`: Configures the logging system with console and SQLite handlers, providing structured logging capabilities.
- `sql_log_handler.py`: SQLite handler for persisting structured logs to database for analysis.
- `__init__.py`: Re-exports logging configuration functions.

## Trading Components (`lib/trading/`)

### Actant Trading System
- `lib/trading/actant/eod/`: End-of-day processing for Actant
- `lib/trading/actant/pnl/`: P&L calculation components
- `lib/trading/actant/sod/`: Start-of-day processing

### Common Trading Utilities (`lib/trading/common/`)
- Trading-related shared utilities and helpers

### TT API Integration (`lib/trading/tt_api/`)
- TT REST API client and related functionality

## Applications (`apps/`)

### Dashboards (`apps/dashboards/`)
- `actant_eod/`: End-of-day dashboard for Actant
- `actant_pnl/`: P&L analysis dashboard with Excel formula implementation
- `ladder/`: Ladder trading interface
- `main/`: Main application entry point

### Unified Dashboard (`apps/unified_dashboard/`)
- `app.py`: Main Dash application setup
- `components/`: Reusable dashboard components
- `pages/`: Individual dashboard pages
- `state/`: State management utilities

## Standalone Packages

### scenario_ladder_standalone/
- **run_scenario_ladder.py** - Standalone version of scenario ladder with minimal dependencies, modified imports for lib/ structure
- **lib/** - Minimal subset of UIKitXv2 libraries needed for scenario ladder
- **data/** - Input/output data directories for mock data and Actant integration
- **requirements.txt** - Python dependencies (dash, pandas, requests, pywinauto, pyperclip)
- **README.md** - Comprehensive setup and usage instructions for standalone deployment

## Utilities
