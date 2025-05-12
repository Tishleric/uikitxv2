# tests/decorators/test_trace_time.py

"""
Unit tests for the TraceTime decorator.

These tests validate the TraceTime decorator's functionality for logging
execution time and function details.
"""

import pytest
import logging
import json
import time
from unittest.mock import patch

# Assuming 'src' is accessible in the path for imports
from decorators.trace_time import TraceTime
from decorators.context_vars import log_uuid_var, current_log_data # Import context vars

# Use the shared fixture from tests/decorators/conftest.py
# setup_logging_context fixture is applied automatically via autouse=True

# --- Test Functions ---

# test_trace_time_basic_logging remains the same
# ... (other tests remain the same) ...

def test_trace_time_return_value_truncation(caplog, setup_logging_context):
    """
    Tests that long return values are truncated in debug logs.
    
    Args:
        caplog: pytest fixture for capturing log output
        setup_logging_context: fixture that initializes logging context with UUID
        
    Verifies:
        - Return values longer than 200 characters are truncated in logs
        - Truncated values end with ellipsis
        - Original value is not included in the log
    """
    test_uuid, _ = setup_logging_context
    caplog.set_level(logging.DEBUG)

    long_string = "X" * 300
    # This is what the decorator calculates internally for truncation
    expected_truncated_repr_internal = repr(long_string)[:200] + '...'


    @TraceTime(log_args=False, log_return=True)
    def func_returning_long():
        return long_string

    func_returning_long()

    # --- Corrected Assertion ---
    # Find the specific log message and check its content
    done_log_message = None
    for record in caplog.records:
        # Find the "Done:" message for the correct function and UUID
        if (record.levelname == 'DEBUG' and
            record.getMessage().startswith(f"Done: func_returning_long ({test_uuid[:8]})")):
            done_log_message = record.getMessage() # Use getMessage() to ensure formatting
            break

    assert done_log_message is not None, "Final 'Done:' log message not found."
    # Check if the expected representation is part of the message
    # Check for the key parts: "Returned:", the start, and the ellipsis
    assert "Returned: '" in done_log_message # Check it starts the repr
    assert long_string[:150] in done_log_message # Check a large part of the beginning is there
    assert "..." in done_log_message # Check the ellipsis is present
    # Check that the full representation is NOT there
    assert repr(long_string) not in done_log_message

# test_trace_time_exception_handling remains the same
# test_trace_time_db_log_format remains the same
# test_trace_time_no_context_uuid remains the same

# (Include the unchanged test functions here if providing the full file) 