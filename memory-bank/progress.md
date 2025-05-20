# Project Progress

## Recent Changes

### Scenario Ladder Range Enhancement
- Modified `scenario_ladder_v1.py` to enhance ladder price range generation:
  - The ladder now always includes the current spot price. If the spot is outside the range of working orders, the ladder expands to include it.
  - Added one extra price increment (tick) as padding at both the top and bottom of the calculated price range.
- Adjusted logic for determining ladder boundaries to consider both processed working orders and the spot price before rounding and padding.
- Ensured early exits for "no data" scenarios correctly account for the availability of spot price.

### Mock Spot Price Implementation
- Added mock spot price (110'085) in scenario_ladder_v1.py for use when USE_MOCK_DATA is True
- Mock spot price is parsed and initialized at application start-up
- Initial spot-price-store is populated with mock values when in mock mode
- Refresh Data button returns mock spot price when in mock mode without making external calls
- Updated docstrings and comments to document this behavior

### Position Calculation Update in Scenario Ladder
- Modified how the position_debug field is calculated in scenario_ladder_v1.py
- Position now reflects accumulated position AFTER orders at that price level are executed
- Projected PnL calculation remains unchanged, still using position BEFORE orders at the current level
- Improves clarity by showing the "post-execution" position at each price level
- Updated all relevant documentation and code comments

### Mermaid Tab UI Enhancements
- Removed the "Diagram Visualization" header from the mermaid tab
- Added a second mermaid diagram showing TT REST API architecture
- Organized both diagrams in separate grid containers for better visual separation
- Provided more comprehensive visualization of system data flow

### TT REST API Integration Enhancement
- Updated scenario_ladder_v1.py to use live data from the TT REST API by default instead of mock data 
- Changed USE_MOCK_DATA flag from True to False, enabling direct connection to TT's services
- Verified code path for live data fetching based on existing implementation and log output
- This provides a more accurate picture of current market orders without requiring manual data updates

### Risk Calculation Enhancement in Scenario Ladder
- Modified risk column calculation in scenario_ladder_v1.py to multiply position by 15.625
- Risk now represents DV01 risk (dollar value of 1 basis point) rather than raw position
- Applied to both calculation passes (above and below spot price)
- Maintains existing position_debug column for raw position display
- No changes to PnL calculation logic
- Added unit test `tests/core/test_mermaid_protocol.py` with a dummy subclass to verify MermaidProtocol method outputs

## 2023-11-14 Project Restructuring

### Completed
- Moved components, core, and utils from src/uikitxv2/ to src/
- Updated all import statements to use the new structure
- Updated Memory Bank documentation with new file paths

### Remaining Structure
- Components directory with all UI component wrappers
- Core directory with BaseComponent class
- Utils directory with color palette
- Component tests
- Memory Bank documentation

### Next Steps
- Consider adding more UI components as needed
- Improve test coverage for components
- Enhance styling options for components

## 2023-11-14 Codebase Pruning (Reverted)

**Note: This pruning was later reverted as decorators and logging functionality was reinstated**

### Originally Completed (Later Reverted)
- Removed all decorator-related code from core and decorators directories
- Removed all database-related code and files
- Removed examples directory and its contents
- Updated pyproject.toml to remove unnecessary dependencies
- Updated Memory Bank documentation (code-index.md and io-schema.md)
- Removed all empty directories (decorators, db, and their subdirectories)
- Cleaned up all cache directories (.mypy_cache, .pytest_cache, .ruff_cache, and all __pycache__ directories)
- Removed empty files (__about__.py)

## 2025-05-01 Decorator Test Suite Implementation

### Completed
- Implemented comprehensive test suite for all decorator modules
- Created test files:
  - `tests/decorators/conftest.py` with shared fixtures for decorator testing
  - `tests/decorators/test_trace_time.py` for function logging decorator tests
  - `tests/decorators/test_trace_cpu.py` for CPU usage tracking decorator tests
  - `tests/decorators/test_trace_memory.py` for memory usage tracking decorator tests
  - `tests/decorators/test_trace_closer.py` for resource tracing decorator tests
- Added tests for basic functionality, error handling, and edge cases
- Included stress tests to ensure robustness with multiple/nested calls
- Added proper mocking for external dependencies (psutil, logging)
- Updated `code-index.md` with new test files

### Next Steps
- Run the tests to validate implementation
- Add integration tests to validate decorators working together
- Consider adding test coverage measurement
- Explore adding performance benchmarks for decorators

## 2025-05-14 Lumberjack Test Suite Implementation

### Completed
- Implemented test suite for lumberjack logging modules
- Created test files:
  - `tests/lumberjack/test_logging_config.py` for logging configuration
  - `tests/lumberjack/test_sqlite_handler.py` for SQLite database logging handler
- Added DataTable component to the component library
- Updated memory bank documentation to reflect current status:
  - Added DataTable to code-index.md
  - Added DataTable entries to io-schema.md
  - Updated demo files in code-index.md
  - Added decorator configuration entries to io-schema.md
  - Added tests for invalid JSON, schema errors, and repeated close operations in
    `tests/lumberjack/test_sqlite_handler.py`

### Next Steps
- Create integration tests for all decorators working together
- Add performance benchmarks for the logging system
- Consider adding more UI components as needed
- Document common usage patterns in README.md and examples

## 2025-05-05 Package Structure Refinement

### Completed
- Consolidated the package structure under `src/` without the uikitxv2 subdirectory
- Updated import patterns to use direct imports (e.g., `from components import Button`)
- Added package-level re-exports in `__init__.py` for easier imports
- Removed references to non-existent files in documentation
- Comprehensive update of memory bank documentation:
  - Updated file paths in code-index.md
  - Revised import examples in io-schema.md
  - Updated dependency flow in systemPatterns.md
  - Fixed code style guidance in .cursorrules
  - Added package structure notes to techContext.md
  - Revised project structure in projectBrief.md

### Next Steps
- Complete integration tests for decorator interactions
- Create performance benchmarks for components
- Verify all imports work correctly throughout the codebase
- Document the new import patterns in README.md

## Recent Fixes

- Fixed Delta (%) y-axis display issue in the dashboard graphs
  - Added explicit numeric type conversion for percentage values
  - Ensured consistent handling across JSON serialization/deserialization
  - Improved table formatting for percentage columns
  - Updated io-schema.md to document the PricingMonkey.%Delta format

- Increased wait times in PricingMonkey data retrieval
  - Extended WAIT_FOR_CELL_RENDERING from 20.0 to 40.0 seconds
  - Increased WAIT_FOR_COPY_OPERATION from 0.2 to 0.5 seconds
  - Improves reliability of data copying before browser window closes

## Completed Tasks

- Improved docstring consistency throughout the codebase [May 10, 2025]
  - Added comprehensive Google-style docstrings to all functions and classes
- Standardized docstring format across all modules
- Focused on decorator modules, components, and utility functions
- No functional code changes were made during this task
- Added Google-style docstrings to all test functions for clarity [May 26, 2025]

# Progress Tracking

## Completed Items

1. Initial repo structure and documentation
2. Abstraction design of BaseComponent
3. Component implementations: Button, ComboBox, DataTable, Graph, Grid, ListBox, RadioButton, Tabs
4. Decorator implementations: TraceTime, TraceCloser, TraceCpu, TraceMemory
5. Logging configuration and SQLite handler
6. Demo application showcasing component usage
7. Unit tests for components and decorators
8. Dashboard application for PricingMonkey automation
9. Dashboard logs view with flow trace and performance data tables
10. Added "Empty Table" button to clear log data from the database tables

## Recently Completed
- Integrated Actant position data into scenario ladder P&L calculations
- Added `convert_tt_special_format_to_decimal` function to parse TT-style price strings
- Added `load_actant_zn_fills` function to read ZN future fills from Actant CSV
- Added `calculate_baseline_from_actant_fills` function to determine net position and realized P&L
- Modified `update_data_with_spot_price` to accept baseline position and P&L
- Enhanced the display to show current position and realized P&L at spot price
- Updated callback to synchronize all data sources (TT working orders, Actant fills, spot price)
- Created `csv_to_sqlite.py` helper module for converting CSV data to SQLite database
- Implemented `load_actant_zn_fills_from_db` function to query fills from SQLite database
- Added graceful fallback to direct CSV reading if SQLite operations fail
- Fixed a bug in `scenario_ladder_v1.py` where a callback would return an incorrect number of outputs if no working orders were found, by ensuring default baseline data is returned.
- Added unit tests for `csv_to_sqlite_table`, `get_table_schema`, and `query_sqlite_table`.
- Added unit tests for TT bond price conversion utilities.
- Enhanced scenario ladder price range in `scenario_ladder_v1.py` to always include the spot price and add top/bottom padding rows.

## In Progress
- Verifying fill price parsing logic is correct for Actant data (from `110'065` format)
- Testing Actant integration with different fill scenarios
- Improving error handling for SQLite database operations

## Known Issues
- Need to extend error handling for malformed Actant data
- Position direction terminology needs to match industry convention (Long/Short vs Buy/Sell)
- SQLite database connection errors might occur if files are locked

## For Investigation

1. Potential memory leak in TraceCpu when used with long-running functions
2. Plotly theme integration issues in dark mode

## Next Tasks

1. Complete integration tests
2. Add more comprehensive dashboard examples
3. Improve error handling in decorators
4. Connect to live Actant data feed when it becomes available
5. Refine visualization of the baseline display
6. Add unit tests for new Actant data processing functions
7. Implement SQLite database schema versioning for future enhancements
