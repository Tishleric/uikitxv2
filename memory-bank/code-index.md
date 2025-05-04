## Core Source Code (src/)

### Components

- `src/components/button.py` - Implementation of the Button component wrapper.
- `src/components/combobox.py` - Implementation of the ComboBox (dropdown) component wrapper.
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

- `src/lumberjack/logging_config.py` - Configures logging with console and SQLite handlers.
- `src/lumberjack/sqlite_handler.py` - Custom logging handler that writes function execution details to SQLite.

### Utils

- `src/utils/colour_palette.py` - Utility for managing color schemes and palettes.

## Documentation & Configuration

- `decorators_overview.md` - Markdown table summarizing available decorators, their purpose, and location.

## Test Suite (tests/)

### Component Tests

- `tests/components/test_button_render.py` - Tests for Button component rendering.
- `tests/components/test_combobox_render.py` - Tests for ComboBox component rendering.
- `tests/components/test_graph_render.py` - Tests for Graph component rendering.
- `tests/components/test_grid_render.py` - Tests for Grid component rendering.
- `tests/components/test_listbox_render.py` - Tests for ListBox component rendering.
- `tests/components/test_radiobutton_render.py` - Tests for RadioButton component rendering.
- `tests/components/test_tabs_render.py` - Tests for Tabs component rendering.

### Decorator Tests

- `tests/decorators/conftest.py` - Shared fixtures for decorator testing including mock resources and functions.
- `tests/decorators/test_trace_time.py` - Tests for the TraceTime decorator with various inputs and scenarios.
- `tests/decorators/test_trace_closer.py` - Tests for the TraceCloser decorator including context tracking and error handling.
- `tests/decorators/test_trace_cpu.py` - Tests for the CPU usage tracking decorator with simulated and real measurements.
- `tests/decorators/test_trace_memory.py` - Tests for the memory usage tracking decorator with mock and real memory allocation.
