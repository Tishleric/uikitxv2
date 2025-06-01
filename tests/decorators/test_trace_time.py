# tests/decorators/test_trace_time.py

import pytest
import logging
import json
import time
from unittest.mock import patch

# Assuming 'src' is accessible in the path for imports
from monitoring.decorators.trace_time import TraceTime
from monitoring.decorators.context_vars import log_uuid_var, current_log_data # Import context vars

# Use the shared fixture from tests/decorators/conftest.py
# setup_logging_context fixture is applied automatically via autouse=True

# --- Test Functions ---

def test_trace_time_basic_logging(caplog, setup_logging_context):
    """Checks DEBUG log output and context update for a successful call."""
    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.DEBUG)

    @TraceTime()
    def add(a, b):
        time.sleep(0.01)
        return a + b

    result = add(2, 3)

    assert result == 5
    assert "duration_s" in test_data

    start_found = any(
        r.getMessage().startswith(f"Starting: add ({test_uuid[:8]})")
        for r in caplog.records
    )
    done_found = any(
        r.getMessage().startswith(f"Done: add ({test_uuid[:8]})")
        for r in caplog.records
    )
    assert start_found
    assert done_found

def test_trace_time_return_value_truncation(caplog, setup_logging_context):
    """Tests that long return values are truncated in debug logs."""
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


def test_trace_time_exception_handling(caplog, setup_logging_context):
    """Ensures duration and error are captured when the function raises."""
    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.DEBUG)

    @TraceTime()
    def boom():
        raise ValueError("bad")

    with pytest.raises(ValueError):
        boom()

    assert test_data.get("error") == "bad"
    assert "duration_s" in test_data
    assert f"Exception in boom ({test_uuid[:8]})" in caplog.text


def test_trace_time_db_log_format(caplog, setup_logging_context):
    """Verifies no FUNC_EXEC_LOG message is emitted."""
    _, _ = setup_logging_context
    caplog.set_level(logging.DEBUG)

    @TraceTime()
    def dummy():
        return "ok"

    dummy()

    db_prefix = getattr(TraceTime, "DB_LOG_PREFIX", "FUNC_EXEC_LOG:")
    assert db_prefix not in caplog.text


def test_trace_time_no_context_uuid(caplog, setup_logging_context):
    """Checks logging when no UUID is present in the context."""
    _, _ = setup_logging_context
    # Remove context before calling
    log_uuid_var.set(None)
    current_log_data.set(None)
    caplog.set_level(logging.DEBUG)

    @TraceTime()
    def simple():
        return 42

    result = simple()

    assert result == 42
    assert any("NO_UUID" in r.getMessage() for r in caplog.records)
