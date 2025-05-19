## Core Source Code (src/)

### Components

- `src/components/button.py` - Implementation of the Button component wrapper.
- `src/components/combobox.py` - Implementation of the ComboBox (dropdown) component wrapper.
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
- `src/decorators/trace_time.py` - Decorator for detailed function logging with timing information.
- `src/decorators/trace_closer.py` - Decorator for managing resource tracing and generating flow trace logs.
- `src/decorators/trace_cpu.py` - Decorator for measuring CPU usage during function execution.
- `src/decorators/trace_memory.py` - Decorator for measuring memory usage during function execution.

### Lumberjack (Logging)

- `src/lumberjack/__init__.py` - Package exports and initialization.
- `src/lumberjack/logging_config.py` - Configures logging with console and SQLite handlers.
- `src/lumberjack/sqlite_handler.py` - Custom logging handler that writes function execution details to SQLite.

### Utils

- `src/utils/colour_palette.py` - Utility for managing color schemes and palettes.

## Documentation & Configuration

- `decorators_overview.md` - Markdown table summarizing available decorators, their purpose, and location.
- `memory-bank/dashboard_functions.md` - Comprehensive list of all functions in dashboard.py and their applied decorators.

## Demo

- `demo/app.py` - Demo application showcasing component usage.

## Dashboard

- `dashboard/dashboard.py` - Main dashboard application with pricing monkey automation interface, analysis visualization, and logs view. Includes functions for flow trace logs querying, performance metrics querying, and emptying log tables. Features a mermaid tab with two diagrams: a project architecture overview and a TT REST API flow diagram.

## Ladder Test Application

- `ladderTest/laddertesting.py` - Dash application to display a TT-style trading ladder with mock data. Includes functionality to scroll to current price levels.
- `ladderTest/price_formatter.py` - Utility function to convert decimal prices to TT bond-style string notation (e.g., "110'005").
- `ladderTest/scenario_ladder_v1.py` - Dash application that displays a scenario ladder based on live working orders fetched from the TT REST API or mock data. It shows prices and user's order quantities with uniform price increments, filling in gaps between actual orders. PnL is calculated based on the position before any orders at the current level, while position_debug shows the accumulated position after orders at that level are executed. The risk column displays position multiplied by 15.625 to represent DV01 risk. Includes mock spot price functionality (110'085) when in mock data mode. Recently fixed a bug where a callback returned an incorrect number of outputs when no working orders were found.
- `ladderTest/csv_to_sqlite.py` - Helper module for converting CSV data to SQLite database tables with query utilities.
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


### Tests (`tests/ttapi/`)
- `tests/ttapi/test_tt_utils.py` - Unit tests for GUID generation, request ID formatting, and sanitization logic in `tt_utils`.

- `tests/ttapi/test_token_manager.py` - Unit tests for TTTokenManager covering token retrieval, auto-refresh, and auth header creation.

- `tests/utils/test_colour_palette.py` - Validates theme defaults and style helper outputs.

- `tests/components/test_mermaid_render.py` - Unit tests for `Mermaid.render` verifying ID propagation, theme styling, and default config merging.

- `tests/components/test_container_render.py` - Unit tests verifying `Container.render` child handling and theme styles.
- `tests/core/test_base_component.py` - Unit tests verifying ID validation and default theme usage in `BaseComponent`.

