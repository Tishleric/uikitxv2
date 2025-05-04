# Decorators Overview

This table provides a summary of the decorators available in the `src/decorators` directory.

| Decorator      | Function                                                                                                                                                                                             | Location                        |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| `@TraceTime`   | Logs function execution start, end, arguments (optional), return value (optional), and duration. Emits DEBUG level logs for entry/exit/call details and INFO level structured logs for database storage. Always Innermost | `src/decorators/trace_time.py` |
| `@TraceCloser` | Manages the lifecycle of a trace context (using `log_uuid_var` and `current_log_data`). Generates a UUID if none exists, captures results/errors, and logs a final `FLOW_TRACE:` message summarizing the call. Always Outermost | `src/decorators/trace_closer.py` |
| `@TraceMemory` | Measures the change in process Resident Set Size (RSS) memory usage before and after the decorated function executes. Logs the delta in MB via an INFO level structured log for database storage.        | `src/decorators/trace_memory.py` |
| `@TraceCpu`    | Measures the change in CPU utilization percentage before and after the decorated function executes. Logs the delta percentage via an INFO level structured log for database storage.                 | `src/decorators/trace_cpu.py`  | 