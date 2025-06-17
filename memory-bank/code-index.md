# Code Index

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
- **monitor.py** - Complete @monitor decorator integrating observability pipeline. Features automatic queue integration, SmartSerializer for argument/result capture, exception traceback preservation, singleton pattern for global queue/writer, sampling rate support (0.0-1.0), process group categorization, and minimal performance overhead (<50µs). Main entry point for function monitoring.
- **context_vars.py** - Shared context variables for tracing and logging decorators
- **trace_time.py** - Decorator for logging function execution time and storing in context
- **trace_closer.py** - Decorator for managing resource tracing and flow trace logs
- **trace_cpu.py** - Decorator for measuring CPU usage delta during execution
- **trace_memory.py** - Decorator for measuring RSS memory usage delta

#### Logging (`lib/monitoring/logging/`)
- **config.py** - Logging configuration with console and SQLite handlers setup
- **handlers.py** - SQLiteHandler processing FLOW_TRACE logs into database tables

#### Serializers (`lib/monitoring/serializers/`)
- **smart.py** - SmartSerializer class for converting Python objects to string representations. Handles all data types including primitives, collections, NumPy arrays, Pandas DataFrames, custom objects, and circular references. Features include sensitive field masking, configurable truncation, and intelligent representation of complex data structures. Core component of the observability system for capturing function arguments and return values.

#### Queues (`lib/monitoring/queues/`)
- **observability_queue.py** - ObservabilityQueue with error-first strategy and zero-loss guarantees. Features dual queue system (unlimited error queue + 10k normal queue), overflow ring buffer (50k capacity), automatic recovery mechanism, comprehensive metrics tracking, thread-safe operations, and rate-limited warnings. Core component ensuring errors are never dropped while managing normal record overflow gracefully.

#### Writers (`lib/monitoring/writers/`)
- **sqlite_writer.py** - Production-ready SQLite writer with BatchWriter thread for observability data persistence. Features include continuous queue draining at configurable intervals, batch inserts with transaction management, WAL mode for concurrent access, comprehensive database statistics tracking, graceful shutdown with final flush, automatic schema creation, and JSON conversion for lazy-serialized objects. Achieves 1500+ records/second sustained write throughput while maintaining data integrity.

#### Performance (`lib/monitoring/performance/`)
- **__init__.py** - Performance module exports: FastSerializer, MetadataCache, get_metadata_cache
- **fast_serializer.py** - Optimized serializer with fast paths for common data types. Features include direct passthrough for primitives (str, int, float, bool, None), lazy serialization for large objects (>10k chars or >1k items), efficient handling of simple collections, fallback to SmartSerializer for complex cases. Achieves < 5µs overhead for common types.
- **metadata_cache.py** - LRU cache for function metadata and frequently used values. Features include configurable size (default 10k entries) and TTL (default 1 hour), thread-safe operations, automatic eviction of stale entries, caching of module/qualname lookups and source file paths. Reduces repeated metadata calculations.

#### Monitoring Tests & Demos (`tests/monitoring/observability/`)
- **demo_parent_child.py** - Demonstrates parent-child relationship tracking with nested function calls. Shows how thread_id, call_depth, and microsecond timestamps enable reconstruction of call hierarchies. Includes SQL queries for call tree visualization and exclusive/inclusive timing analysis.

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
- **__init__.py** - Exports BondFutureOption class and analysis functions

- **pricing_engine.py** - Core bond future option pricing engine (CTO-validated):
  - `BondFutureOption` - Main class for Bachelier model pricing
  - Future DV01 and convexity-based Greeks calculations
  - Price/yield volatility conversions
  - Comprehensive Greeks: delta, gamma, vega, theta, and higher-order
  - Both F-space (price) and Y-space (yield) Greeks

- **analysis.py** - Refactored analysis utilities:
  - `solve_implied_volatility()` - Newton-Raphson solver for backing out vol
  - `calculate_all_greeks()` - Calculate all Greeks with proper scaling
  - `generate_greek_profiles()` - Generate Greeks across price scenarios (±20 points)
  - `analyze_bond_future_option_greeks()` - Main analysis function
  - `validate_refactoring()` - Validation against original implementation

- **demo_profiles.py** - Demonstration code for Greek profile visualization:
  - Generates Greek profiles across market scenarios
  - Creates matplotlib plots for key Greeks (delta, gamma, vega, theta)
  - Exports data to CSV for further analysis
  - Shows scenario analysis and moneyness effects
  - Saves outputs to `output/` subdirectory

- **output/** - Directory for generated outputs (CSV, PNG files)
  - Contains .gitignore to exclude generated files
  - Greek profile CSV files and visualization plots saved here

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
- **app.py** - Main unified dashboard integrating all tabs into single application with sidebar navigation system, comprehensive callback management, namespace isolation with prefixed functions per dashboard, advanced state management through data stores, professional UI theming, complete Actant EOD dashboard implementation with 15+ helper functions and interactive visualizations, and fixed Actant PnL integration with early callback registration to prevent double-click issue

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

## Remaining Original Locations

### TTRestAPI Directory
- **examples/** - Various TT API usage examples
- Response JSON files for reference
- Token files and other configurations

## Entry Points
- **run_actant_eod.py** - Entry point for ActantEOD dashboard (port 8050)
- **run_actant_sod.py** - Entry point for ActantSOD processing
- **run_scenario_ladder.py** - Entry point for Scenario Ladder dashboard (port 8051)
- **pyproject.toml** - Package configuration with dependencies

## Tests Directory Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_imports.py          # Verify all imports work
├── components/              # Component tests
├── monitoring/              # Decorator and logging tests
├── trading/                 # Trading utility tests
└── integration/             # Dashboard integration tests
```

## Scripts (`scripts/`)
- **actant_eod/process_actant_json.py** - Processes Actant JSON output into flattened CSV and SQLite format
- **actant_eod/data_integrity_check.py** - Comprehensive data integrity verification for ActantEOD pipeline
- **actant_eod/verify_th_pnl.py** - Simple verification script for Th PnL data integrity
- **actant_sod/pricing_monkey_to_actant.py** - Integration script that retrieves PM data and processes through actant logic
- **actant_pnl_formula_extractor.py** - Extract Excel formulas from actantpnl.xlsx for analysis
- **run_actant_pnl_demo.py** - Run the Actant PnL dashboard in standalone mode for testing

## Data Structure (`data/`)
```
data/
├── input/
│   ├── eod/              # ActantEOD input files
│   ├── sod/              # ActantSOD input files  
│   ├── ladder/           # Ladder input files
│   ├── actant_pnl/       # Actant PnL CSV files (e.g., GE_XCME.ZN_*.csv)
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

## Utilities
- `lib/uikitxv2.egg-info/`: Package metadata and entry points

## Testing (`tests/`)
- Comprehensive test coverage for components, decorators, and trading logic
- Tests follow the same structure as the source code

## Migration Scripts (`scripts/migration/`)
- Tools for migrating from old structure to new architecture

## Memory Bank (`memory-bank/`)

### Documentation Files
- `activeContext.md`: Current development focus and immediate next steps
- `code-index.md`: This file - comprehensive map of all code modules
- `io-schema.md`: Canonical list of all inputs, outputs, constants, and environment variables
- `productContext.md`: Product vision and user experience goals
- `progress.md`: Development progress tracking
- `projectBrief.md`: High-level project overview and objectives
- `systemPatterns.md`: Architectural patterns and design decisions
- `techContext.md`: Technology stack and constraints
- `.cursorrules`: Coding standards and AI assistant guidelines

### Feature Documentation (`memory-bank/PRDeez/`)
- `logsystem.md`: Original observability system design brief
- `observability-implementation-plan.md`: Refined implementation plan combining original brief with technical review feedback. Includes phases, concrete API specs, performance targets, and migration strategy.

### Actant PnL Analysis (`memory-bank/actant_pnl/`)
- `analysis/`: Excel formula analysis and documentation
- `implementation/`: Dashboard implementation notes


- `implementation/`: Dashboard implementation notes

