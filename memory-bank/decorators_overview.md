# Decorators Overview

This table provides a summary of the decorators available in the `src/decorators` directory.

| Decorator      | Function                                                                                                                                                                                             | Location                        |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| `@TraceTime`   | Logs function execution start, end, arguments (optional), return value (optional), and duration. Emits DEBUG level console logs for entry/exit/call details. Stores timing data in `current_log_data`. Always Innermost. | `src/decorators/trace_time.py` |
| `@TraceCloser` | Manages the lifecycle of a trace context (using `log_uuid_var` and `current_log_data`). Generates a UUID if none exists, captures results/errors, and logs a final `FLOW_TRACE:` message (using data from other decorators) to the database. Always Outermost. | `src/decorators/trace_closer.py` |
| `@TraceMemory` | Measures the change in process Resident Set Size (RSS) memory usage before and after the decorated function executes. Stores the delta in MB in `current_log_data`.        | `src/decorators/trace_memory.py` |
| `@TraceCpu`    | Measures the change in CPU utilization percentage before and after the decorated function executes. Stores the delta percentage in `current_log_data`.                 | `src/decorators/trace_cpu.py`  | 