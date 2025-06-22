# Dashboard Functions & Decorator Coverage

This document catalogs all functions in `dashboard.py` and lists the decorators applied to each.

## User Interface Callbacks

| Function Name | Purpose | Applied Decorators |
|--------------|---------|-------------------|
| `update_option_blocks` | Updates option blocks based on number selection | `@TraceCloser`, `@TraceTime` |
| `handle_update_sheet_button_click` | Main action for "Run Pricing Monkey Automation" | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |
| `update_graph_from_combobox` | Updates graph based on Y-axis selection | `@TraceCloser`, `@TraceTime` |
| `handle_analysis_interactions` | Handles Analysis tab interactions (refresh, selection changes) | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |
| `toggle_view` | Toggles between Graph and Table views | `@TraceCloser`, `@TraceTime` |
| `toggle_logs_tables` | Toggles between Flow Trace and Performance tables | `@TraceCloser`, `@TraceTime` |
| `refresh_log_data` | Refreshes log data when button is clicked | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |

## Data Processing Functions

| Function Name | Purpose | Applied Decorators |
|--------------|---------|-------------------|
| `create_analysis_graph` | Creates graph figure from data dictionary | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |
| `prepare_table_data` | Transforms nested data for table display | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |
| `create_option_input_block` | Creates UI component for option input | None |
| `create_logs_tab` | Creates UI structure for logs tab | None |

## Database & Logging Functions

| Function Name | Purpose | Applied Decorators |
|--------------|---------|-------------------|
| `verify_log_database` | Verifies log database tables exist | `@TraceCloser`, `@TraceTime` |
| `query_flow_trace_logs` | Queries flowTrace table from database | `@TraceCloser`, `@TraceTime` |
| `query_performance_metrics` | Queries AveragePerformance table from database | `@TraceCloser`, `@TraceTime` |
| `setup_logging_traced` | Wrapper for setup_logging | `@TraceCloser`, `@TraceTime` |
| `shutdown_logging_traced` | Wrapper for shutdown_logging | `@TraceCloser`, `@TraceTime` |

## External Function Wrappers

| Function Name | Purpose | Applied Decorators |
|--------------|---------|-------------------|
| `run_pm_automation_traced` | Wrapper for run_pm_automation | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |
| `get_market_movement_data_df_traced` | Wrapper for get_market_movement_data_df | `@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime` |

## Decorator Categories

### Full Tracing Stack
Functions with the complete decorator stack (`@TraceCloser`, `@TraceCpu`, `@TraceMemory`, `@TraceTime`) are:

- `handle_update_sheet_button_click` - Primary user action
- `handle_analysis_interactions` - Complex data retrieval and processing
- `create_analysis_graph` - Computationally intensive visualization
- `prepare_table_data` - Data transformation
- `refresh_log_data` - Database operations
- `run_pm_automation_traced` - External module interaction
- `get_market_movement_data_df_traced` - External data fetch

### Basic Timing
Functions with basic timing only (`@TraceCloser`, `@TraceTime`) are:

- `update_option_blocks` - UI component update
- `update_graph_from_combobox` - UI component update
- `toggle_view` - UI state toggle
- `toggle_logs_tables` - UI state toggle
- `verify_log_database` - Database check
- `query_flow_trace_logs` - Simple database query
- `query_performance_metrics` - Simple database query
- `setup_logging_traced` - Application startup
- `shutdown_logging_traced` - Application shutdown

### No Decorators
Functions with no decorators are primarily UI initialization functions that run once:

- `create_option_input_block` - UI component creation
- `create_logs_tab` - UI component creation

## Notes

- Arguments are logged (`log_args=True`) for: `query_flow_trace_logs`, `refresh_log_data`, `run_pm_automation_traced`
- Return values are not logged for any function (`log_return=False`)
- The core logging setup is performed using the `setup_logging_traced` wrapper 