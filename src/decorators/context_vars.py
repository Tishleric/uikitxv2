"""
Context variables for decorator communication.

This module defines shared context variables used by the tracing decorators
to communicate and share data across the execution context.
"""

import contextvars

# Shared context variable for the unique log identifier
log_uuid_var = contextvars.ContextVar('log_uuid', default=None)

# Shared context variable for passing data between decorators in a single call
current_log_data = contextvars.ContextVar('current_log_data', default=None)

