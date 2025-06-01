import contextvars

# Shared context variables for tracing and logging decorators
"""
Shared context variables for tracing and logging decorators.

This module provides context variables that allow various decorator 
components to share information during function execution.
"""

# Shared context variable for the unique log identifier
log_uuid_var = contextvars.ContextVar('log_uuid', default=None)
"""ContextVar: Stores a unique identifier for tracking function calls.

This context variable stores a UUID that's used to correlate logs
across multiple decorators applied to the same function call.
"""

# Shared context variable for passing data between decorators in a single call
current_log_data = contextvars.ContextVar('current_log_data', default=None)
"""ContextVar: Stores a dictionary of data shared between decorators.

This context variable stores execution information like timing data,
CPU usage, memory usage, etc. that's shared between decorators.
"""

