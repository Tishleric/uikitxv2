# Code Index (uikitxv2)

## Table of Contents
1. [Core System Components](#core-system-components)
2. [Trading Modules](#trading-modules)
3. [Main Dashboard](#main-dashboard)
4. [Tests](#tests)
5. [Scripts](#scripts)
6. [Infrastructure](#infrastructure)

---

## Core System Components

### lib/components/
The Dash component library with Material Design themed UI components.

#### lib/components/core/
- **base_component.py**: Abstract base class for all components with theme support and rendering methods
- **protocols.py**: Python protocols defining interfaces for theming, HTML attributes, and Mermaid diagrams

#### lib/components/basic/
- **button.py**: Button component with multiple variants (primary, secondary, danger, etc.)
- **checkbox.py**: Checkbox with label support  
- **combobox.py**: Dropdown select component with search and multi-select
- **container.py**: Layout container with theme-aware styling
- **grid.py**: Responsive grid layout using Material Design breakpoints
- **input.py**: Text input field with various types (text, number, password, etc.)
- **listbox.py**: Multi-select list component
- **radiobutton.py**: Radio button groups
- **slider.py**: Range slider with single/dual handle support
- **textarea.py**: Multi-line text input

#### lib/components/advanced/
- **datatable.py**: Feature-rich data table with sorting, filtering, and pagination
- **graph.py**: Plotly graph wrapper with theme integration
- **markdown.py**: Markdown renderer with syntax highlighting
- **tabs.py**: Tab container for multi-panel layouts

#### lib/components/themes/
- **colour_palette.py**: Material Design color palette implementation

### lib/monitoring/
Observability and monitoring infrastructure for tracking function execution, performance, and errors.

#### lib/monitoring/decorators/
- **monitor.py**: Main @monitor decorator for automatic function instrumentation
- **trace_closer.py**: @trace_closer for closing monitoring contexts
- **trace_cpu.py**: @trace_cpu for CPU usage tracking
- **trace_all.py**: @trace_all for comprehensive tracing
- **variable_tracker.py**: @track_variables for monitoring variable changes
- **context_vars.py**: Thread-safe context management for tracing

#### lib/monitoring/logging/
- **config.py**: Centralized logging configuration
- **handlers.py**: SQLite and file logging handlers

#### lib/monitoring/performance/
- **fast_serializer.py**: High-performance JSON serialization
- **metadata_cache.py**: LRU cache for function metadata

#### lib/monitoring/retention/
- **manager.py**: Log retention and cleanup management
- **controller.py**: Retention policy enforcement

#### lib/monitoring/writers/
- **sqlite_writer.py**: SQLite database writer for monitoring data

#### lib/monitoring/queues/
- **observatory_queue.py**: Thread-safe queue for observatory data collection

---

## Trading Modules

### lib/trading/bond_future_options/
Bond future options pricing using the Bachelier model with factory/facade architecture.

**api.py**: Main API for Greek calculations using Bachelier model. Provides `calculate_greeks()` for single option and `batch_calculate_greeks()` for multiple options. Contains all safeguards including MIN_PRICE_SAFEGUARD=1/64, MAX_IMPLIED_VOL=1000, tolerance=1e-6, and moneyness-based initial guesses.

**analysis.py**: Core implementation of Black-Scholes-Merton model adapted for bond futures. Contains the `ImpliedVolCalculator` class with Newton-Raphson solver and all Greek calculation methods. Handles edge cases with safeguards.

**bond.py**: Bond pricing and yield calculation utilities. Provides methods for bond price/yield conversions and duration calculations using continuous compounding.

**futures.py**: Bond futures contract specifications and pricing. Handles conversion factors and delivery option calculations.

**option_model_interface.py**: Protocol defining the standard interface that all option pricing models must implement. Ensures consistent API across different model implementations.

**models/bachelier_v1.py**: Wrapper implementing OptionModelInterface for the existing Bachelier implementation. Translates between the generic interface and the specific API of the current model.

**model_factory.py**: Factory pattern implementation for creating option pricing models. Maintains a registry of available models and provides methods to instantiate them by name.

**greek_calculator_api.py**: High-level facade providing a simple interface for Greek calculations. Handles model selection, parameter validation, and provides both single and batch processing capabilities.

### lib/trading/actant/
Actant trading system integration modules.

#### lib/trading/actant/eod/
- **data_service.py**: EOD data service with caching and processing
- **parser.py**: JSON parser for Actant EOD files
- **models.py**: Data models for EOD positions and scenarios

#### lib/trading/actant/pnl/
- **calculator.py**: P&L calculation engine using Excel formulas
- **formula_parser.py**: Excel formula parsing and evaluation
- **parser.py**: CSV parser for Actant P&L files  
- **models.py**: Data models for P&L calculations

#### lib/trading/actant/sod/
- **parser.py**: CSV parser for start-of-day positions
- **processor.py**: SOD data processing and transformations
- **models.py**: Data models for SOD positions
- **validator.py**: Data validation for SOD files

#### lib/trading/actant/spot_risk/
- **parser.py**: CSV parser for spot risk analysis files with mixed futures/options. Conditionally skips rows based on filename - skips row 1 for original format files, no skip for processed files.
- **calculator.py**: Greek calculator for spot risk positions using GreekCalculatorAPI; extracts future prices from DataFrame and processes options in batch
- **time_calculator.py**: Time to expiry calculations with CME conventions

**calculator.py**: SpotRiskGreekCalculator class that processes CSV files and calculates Greeks using the GreekCalculatorAPI. Handles future price extraction, batch Greek calculations, and adds all Greek columns to the DataFrame. Contains error handling that raises ValueError when no future price is found.

**csv_parser.py**: Parses CSV files exported from Actant spot risk reports. Converts all column names to lowercase, handles numeric parsing, and provides structured DataFrames for downstream processing.

**schema.sql**: SQLite database schema for spot risk data storage. Defines three tables: spot_risk_sessions (for tracking data loads), spot_risk_raw (for storing original CSV data), and spot_risk_calculated (for storing calculated Greeks). Includes indexes and a convenience view for latest calculations.

**db_init.py**: Database initialization script that creates the SQLite database from schema.sql. Includes functions to initialize the database and verify the schema. Creates the database at data/output/spot_risk/spot_risk.db with proper foreign key constraints and indexes.

### lib/trading/ladder/
Scenario ladder functionality for options analysis.

- **csv_to_sqlite.py**: Converts CSV data to SQLite for ladder
- **price_formatter.py**: TT price format conversions (decimals, fractions, special formats)

### lib/trading/tt_api/
Trading Technologies API integration.

- **config.py**: TT API configuration and endpoints
- **token_manager.py**: OAuth token management with auto-refresh
- **tt_utils.py**: Utility functions for TT API interactions

### lib/trading/pricing_monkey/
Legacy pricing system integration.

---

## Main Dashboard

### apps/dashboards/main/app.py
The main integrated dashboard application combining all features:
- Pricing Monkey automation interface
- Market movement analysis with scenario modeling
- Greek analysis for bond future options using Bachelier model
- Flow trace logs and performance metrics viewer
- Project documentation browser
- Scenario ladder for real-time position monitoring
- Actant EOD data visualization
- Actant P&L dashboard
- Observatory for monitoring decorated functions

### apps/dashboards/actant_pnl/pnl_dashboard.py: Main dashboard implementation for actant PnL analysis. Creates the UI layout with formula comparison table, dropdown for formula selection, and Taylor approximation error display. Integrates with CSV parser to load and display option Greek calculations.

### apps/dashboards/spot_risk/__init__.py: Package initialization for Spot Risk dashboard. Exports register_callbacks for main app integration.

### apps/dashboards/spot_risk/app.py: Entry point for Spot Risk dashboard. Creates Dash app instance, sets up layout, and registers callbacks. Can run standalone or be integrated into main dashboard.

### `apps/dashboards/spot_risk/controller.py`
Core controller for Spot Risk dashboard coordinating data loading, Greek calculations, and filtering. Loads Actant CSV data, integrates with SpotRiskGreekCalculator for bachelier option pricing, finds ATM strikes using delta ~0.5 heuristic. Supports position filtering, expiry grouping, and Greek profile generation with Taylor series expansion. Enhanced with smart column detection for 'expiry_date', 'pos.position', Greek column mapping (delta→delta_F, vega→vega_price, etc.), and fallback logic for alternative column names. Generates Greek profiles both unified and grouped by expiry with full position data including current Greek values for hover tooltips.

### apps/dashboards/spot_risk/views.py
UI components and layout for Spot Risk dashboard. Creates header, control panels, Greek selection checkboxes, view toggle, and data display sections. Fixed structural issue - graph container is now a sibling of table container (not a child) to allow proper toggle visibility. Uses wrapped UI components with default_theme styling.

### apps/dashboards/spot_risk/callbacks.py
Core callback functions for the Spot Risk dashboard. Includes update_spot_risk_table for Greek calculations and table population, greek_groups_changed for dynamic column visibility, toggle_view for switching between table/graph views, track_view_state for monitoring active view mode, update_greek_graphs for generating Greek profile visualizations grouped by expiry date with section headers and per-expiry statistics, toggle_refresh_interval for auto-refresh control, and export_to_csv placeholder. All callbacks use SpotRiskController for business logic and are decorated with @monitor for observability. Successfully displays Greek profiles organized by expiry with position markers and ATM strike indicators.

### apps/dashboards/actant_preprocessing/__init__.py: Package init file for the Actant Preprocessing dashboard module.

---

## Tests

### tests/actant_pnl/
- **test_calculator.py**: Tests for P&L calculation engine
- **test_csv_parser.py**: Tests for CSV parsing functionality
- **test_dashboard_fix.py**: Dashboard integration tests
- **test_date_parsing.py**: Date parsing edge case tests
- **test_formula_parser.py**: Excel formula parsing tests
- **test_pnl_models.py**: P&L data model tests

### tests/actant_spot_risk/

**test_greek_calculator.py**: Unit tests for SpotRiskGreekCalculator. Tests single option calculation, batch processing with multiple options, and error handling for edge cases. Validates all Greek outputs and column additions.

**test_calculator_error_handling.py**: Tests error handling in the SpotRiskGreekCalculator. Validates that the calculator raises ValueError when no future price is found, providing clear error messages about what was searched.

**test_full_pipeline.py**: End-to-end integration test processing actual CSV file (bav_analysis_20250708_104022.csv). Tests the complete pipeline from CSV parsing through Greek calculations to output file creation. Handles column name case differences correctly.

### tests/bond_future_options/

**test_api_alignment.py**: Comprehensive tests validating that api.py implementation matches app.py behavior exactly. Tests tolerance=1e-6, MAX_IMPLIED_VOL=1000, MIN_PRICE_SAFEGUARD=1/64, moneyness-based initial guesses, and all safeguards.

**test_factory_pattern.py**: Tests for the factory/facade architecture. Validates ModelFactory registration and instantiation, OptionModelInterface implementation, and GreekCalculatorAPI functionality including model selection and batch processing.

### tests/components/
- **test_button_render.py**: Button component rendering tests
- **test_combobox_render.py**: Combobox component tests
- **test_container_render.py**: Container layout tests
- **test_datatable_render.py**: DataTable component tests
- **test_factory_component_parity.py**: Factory pattern implementation tests
- **test_graph_render.py**: Graph component rendering tests
- **test_grid_render.py**: Grid layout system tests

### tests/decorators/
- **test_trace_closer.py**: Trace closer decorator tests
- **test_trace_cpu.py**: CPU tracing decorator tests
- **test_track_variables.py**: Variable tracking tests

### tests/monitoring/
- **test_circuit_breaker.py**: Circuit breaker pattern tests
- **test_resource_monitor.py**: Resource monitoring tests

### tests/monitoring/observability/
Comprehensive test suite for monitoring decorators and observatory functionality.

---

## Scripts

### scripts/actant_eod/
- **data_integrity_check.py**: Validates EOD data integrity
- **process_eod_json.py**: Processes raw EOD JSON files

### scripts/actant_sod/
- **pricing_monkey_to_actant.py**: Converts Pricing Monkey format to Actant

### scripts/
- **bond_options_csv_example.py**: Example script for bond options CSV processing
- **actant_pnl_formula_extractor.py**: Extracts formulas from Actant P&L files
- **process_spot_risk.py**: User-friendly command-line script for processing spot risk CSV files with Greek calculations. Preserves timestamps in output filenames and uses adjtheor as primary price source
- **run_spot_risk_processing.bat**: Windows batch file that ensures Anaconda Python is used for spot risk processing. Resolves Python path conflicts between standalone and Anaconda installations

### volatility_comparison/
- **compare_volatilities.py**: Calculates theoretical volatility and compares with Actant and PM data. Creates pivot tables and comparison outputs with proper timestamp tracking
- **volatility_tester.py**: Tests volatility calculations for bond future options. Includes comparison with different models and CSV output generation

---

## Infrastructure

### infra/
- **aws-cloud-development-plan.md**: Comprehensive AWS deployment plan
- **migration-requirements-table.md**: Cloud migration requirements matrix
- **architecture-diagram-enhanced.md**: System architecture documentation

### memory-bank/
Project knowledge base and documentation:
- **projectbrief.md**: Project overview and objectives
- **productContext.md**: Product requirements and context
- **systemPatterns.md**: Design patterns and architecture decisions
- **techContext.md**: Technical stack and constraints
- **activeContext.md**: Current development focus
- **progress.md**: Development progress tracking
- **code-index.md**: This file - comprehensive code inventory
- **io-schema.md**: Input/output schemas and data contracts
- **PRDeez/**: Product requirement documents

## Monitoring & Logging

**app.py**: Standalone observatory dashboard application for development and testing. Creates a simple dashboard with flow trace table from the observatory monitoring system. Uses port 8052 for development.

**callbacks.py**: Observatory dashboard callbacks including refresh functionality and navigation. Handles loading trace data from the observatory database and updating the dashboard display.

**views.py**: Observatory dashboard view components. Creates the layout with a DataTable showing recent function traces, message details, and execution context from the monitoring system.

**app.py**: Spot Risk dashboard module initialization. Exports create_spot_risk_content and register_callbacks functions for integration with the main dashboard.

**app.py**: Standalone Spot Risk dashboard application for development and testing. Creates a Dash app with proper assets configuration. Uses port 8055 for development.

**views.py**: Pure presentation layer for spot risk dashboard. Defines get_column_definitions() to organize columns by Greek category (base, 1st/2nd/3rd order, cross, other). Creates complete UI layout with styled header (title, timestamp display, refresh button, auto-refresh controls), filter controls panel (expiry dropdown, type radio buttons, strike range slider), Greek groups section (checkboxes for column visibility), view controls section (table/graph toggle, model selector, export button), and data display with DataTable (pagination, theme styling, no-data message, graph placeholder). Uses wrapped components throughout with consistent theme styling. Includes hidden stores for state management and interval component for auto-refresh. Accepts controller parameter for data access.

**callbacks.py**: Spot Risk dashboard callbacks (currently placeholder). Will handle refresh data, filter updates, Greek selection, export functionality, and auto-refresh toggle.

**controller.py**: Spot Risk Dashboard Controller - handles data loading, processing, and state management. Core controller that manages CSV discovery, data loading, Greek calculations, filtering, and profile generation. Supports both synchronous Greek calculation and asynchronous reading from pre-calculated CSV files for better performance.
