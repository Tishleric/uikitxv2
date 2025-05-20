## Core Source Code (src/)

- `src/__init__.py` - Main package initializer, re-exports components.

### Components

- `src/components/button.py` - Implementation of the Button component wrapper.
- `src/components/combobox.py` - Implementation of the ComboBox (dropdown) component wrapper.
- `src/components/container.py` - Wrapper for `dbc.Container` for themed layout, handling child component rendering.
- `src/components/datatable.py` - Implementation of the DataTable component wrapper for displaying tabular data.
- `src/components/graph.py` - Implementation of the Graph component wrapper for Plotly figures.
- `src/components/grid.py` - Implementation of the Grid layout component for arranging multiple UI components.
- `src/components/listbox.py` - Implementation of the ListBox component wrapper for multi-selection.
- `src/components/mermaid.py` - Implementation of the Mermaid component wrapper for rendering diagrams.
- `src/components/radiobutton.py` - Implementation of the RadioButton component wrapper.
- `src/components/tabs.py` - Implementation of the Tabs component wrapper for tabbed interfaces.

### Core

- `src/core/base_component.py` - Abstract base class for all UI components.
- `src/core/mermaid_protocol.py` - Protocol defining the interface for Mermaid diagram components.

### Decorators

- `src/decorators/context_vars.py` - Shared context variables for tracing and logging decorators.
- `src/decorators/trace_time.py` - Decorator for logging function execution time, optionally arguments/return values, and storing timing in shared context.
- `src/decorators/trace_closer.py` - Decorator for managing resource tracing and generating flow trace logs.
- `src/decorators/trace_cpu.py` - Decorator for measuring CPU usage delta during function execution and storing it in shared context.
- `src/decorators/trace_memory.py` - Decorator for measuring RSS memory usage delta during function execution and storing it in shared context.

### Lumberjack (Logging)

- `src/lumberjack/__init__.py` - Package exports and initialization.
- `src/lumberjack/logging_config.py` - Configures logging with console and SQLite handlers.
- `src/lumberjack/sqlite_handler.py` - Custom handler processing `FLOW_TRACE:` logs into `flowTrace` and `AveragePerformance` SQLite tables.

### Utils

- `src/utils/colour_palette.py` - Defines the `Theme` dataclass, `default_theme`, and provides utility functions for default component styling.

### PricingMonkey

- `src/PricingMonkey/pMoneyAuto.py` - Automates Pricing Monkey workflow for multiple options using Excel, processes results, and writes to a sheet.
- `src/PricingMonkey/pMoneyMovement.py` - Automates browser interaction to retrieve market movement data from Pricing Monkey for analysis.

## Documentation & Configuration

- `decorators_overview.md` - Markdown table summarizing available decorators, their purpose, and location.
- `memory-bank/dashboard_functions.md` - Comprehensive list of all functions in dashboard.py and their applied decorators.

## Demo

- `demo/app.py` - Dash demo application showcasing UI component usage, Mermaid diagrams, and decorator logging integration with a log viewer tab.
- `demo/flow.py` - Simulates a multi-step trading day workflow (SOD, TT Handoff, CME/Internal Exec, Actant Analytics) with full decorator tracing.
- `demo/query_runner.py` - Executes SQL queries from `queries.yaml` against a demo SQLite database, with decorator tracing on query functions.
- `demo/run_queries_demo.py` - Script to run and demonstrate the decorated functions in `query_runner.py`.
- `demo/test_decorators.py` - Contains dummy functions with various decorator combinations to test tracing and logging outputs.

## Dashboard

- `dashboard/dashboard.py` - Main dashboard application with pricing monkey automation interface, analysis visualization, and logs view. Includes functions for flow trace logs querying, performance metrics querying, and emptying log tables. Features a mermaid tab with two diagrams: a project architecture overview and a TT REST API flow diagram.

## Ladder Test Application

- `ladderTest/laddertesting.py` - Dash application to display a TT-style trading ladder with mock data. Includes functionality to scroll to current price levels.
- `ladderTest/price_formatter.py` - Utility function to convert decimal prices to TT bond-style string notation (e.g., "110'005").
- `ladderTest/scenario_ladder_v1.py` - Advanced scenario ladder Dash app. Displays working orders, spot price (via Pricing Monkey), and calculates P&L from a baseline derived from Actant SOD fills (CSV/SQLite). Features dynamic range, DV01 risk, and breakeven calculations.
- `ladderTest/csv_to_sqlite.py` - Helper module for converting CSV data to SQLite database tables with query utilities.
- `ladderTest/zn_price_tracker_app.py` - Dash application to periodically fetch and display ZN Jun25 instrument data from the TT REST API.
- `tests/ladderTest/test_scenario_ladder_v1.py` - Unit tests covering price ladder calculations and PnL updates with mocked TT REST API responses.
- `tests/ladderTest/test_csv_to_sqlite.py` - Unit tests for the CSV-to-SQLite conversion helpers.
- `tests/ladderTest/test_price_formatter.py` - Unit tests for TT bond price conversion utilities.

## TT REST API Integration (TTRestAPI/)

- `TTRestAPI/tt_config.py` - Configuration for TT REST API keys, secrets, and environment settings.
- `TTRestAPI/token_manager.py` - Manages TT REST API authentication tokens, including acquisition, storage, and refresh logic. Supports UAT, SIM, and LIVE environments.
- `TTRestAPI/tt_utils.py` - Utility functions for TT REST API integration, such as GUID generation and request ID formatting.
- `TTRestAPI/api_example.py` - Comprehensive example demonstrating various API calls using the token manager.
- `TTRestAPI/get_token_cli.py` - Command-line tool for fetching and managing TT REST API tokens.

### TT REST API Examples (`TTRestAPI/examples/`)
- `TTRestAPI/examples/simple_api_call.py` - Basic example of fetching market data.
- `TTRestAPI/examples/get_cme_products.py` - Fetches and lists products for the CME market.
- `TTRestAPI/examples/get_zn_instruments.py` - Fetches and lists instruments for the ZN (10-Year T-Note) product.
- `TTRestAPI/examples/get_zn_instrument_details.py` - Fetches detailed information for a specific ZN instrument.
- `TTRestAPI/examples/get_my_algo_ids.py` - Fetches and lists ADL algorithm IDs and names.
- `TTRestAPI/examples/get_algo_orders.py` - Fetches working orders, with logic to identify orders related to a specific algorithm.
- `TTRestAPI/examples/get_order_enumerations.py` - Fetches and saves enumeration definitions (e.g., for order status, side, type) from the `/ttledger/orderdata` endpoint.


## Tests

- `tests/dashboard/test_dashboard_callbacks.py` - Unit tests for dashboard callbacks such as option block updates and log refresh logic.

- `tests/ttapi/test_tt_utils.py` - Unit tests for GUID generation, request ID formatting, and sanitization logic in `tt_utils`.

- `tests/ttapi/test_token_manager.py` - Unit tests for TTTokenManager covering token retrieval, auto-refresh, and auth header creation.

- `tests/utils/test_colour_palette.py` - Validates theme defaults and style helper outputs.

- `tests/components/test_mermaid_render.py` - Unit tests for `Mermaid.render` verifying ID propagation, theme styling, and default config merging.

- `tests/components/test_container_render.py` - Unit tests verifying `Container.render` child handling and theme styles.
- `tests/core/test_base_component.py` - Unit tests verifying ID validation and default theme usage in `BaseComponent`.
- `tests/core/test_mermaid_protocol.py` - Ensures abstract methods defined in `MermaidProtocol` return expected structures when implemented.

