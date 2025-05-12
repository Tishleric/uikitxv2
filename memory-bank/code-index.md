## Core Source Code (src/)

### Components

- `src/components/button.py` - Implementation of the Button component wrapper.
- `src/components/combobox.py` - Implementation of the ComboBox (dropdown) component wrapper.
- `src/components/datatable.py` - Implementation of the DataTable component wrapper for displaying tabular data.
- `src/components/graph.py` - Implementation of the Graph component wrapper for Plotly figures.
- `src/components/grid.py` - Implementation of the Grid layout component for arranging multiple UI components.
- `src/components/listbox.py` - Implementation of the ListBox component wrapper for multi-selection.
- `src/components/radiobutton.py` - Implementation of the RadioButton component wrapper.
- `src/components/tabs.py` - Implementation of the Tabs component wrapper for tabbed interfaces.

### Core

- `src/core/base_component.py` - Abstract base class for all UI components.

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

- `demo/app.py`