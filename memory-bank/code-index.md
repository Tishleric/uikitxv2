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
- **context_vars.py** - Shared context variables for tracing and logging decorators
- **trace_time.py** - Decorator for logging function execution time and storing in context
- **trace_closer.py** - Decorator for managing resource tracing and flow trace logs
- **trace_cpu.py** - Decorator for measuring CPU usage delta during execution
- **trace_memory.py** - Decorator for measuring RSS memory usage delta

#### Logging (`lib/monitoring/logging/`)
- **config.py** - Logging configuration with console and SQLite handlers setup
- **handlers.py** - SQLiteHandler processing FLOW_TRACE logs into database tables

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
- **app.py** - Main FRGM Trade Accelerator dashboard with PricingMonkey integration

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

## Data Structure (`data/`)
```
data/
├── input/
│   ├── eod/              # ActantEOD input files
│   ├── sod/              # ActantSOD input files  
│   ├── ladder/           # Ladder input files
│   └── reference/        # Reference data (actant.csv, SampleZNSOD.csv)
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

