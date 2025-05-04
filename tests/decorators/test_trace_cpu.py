# tests/decorators/test_trace_cpu.py

import pytest
import logging
import json
import uuid
import time
import contextvars
from unittest.mock import patch, MagicMock

# Assuming 'src' is accessible in the path for imports
# Adjust if your test setup requires different import paths
from decorators.trace_cpu import TraceCpu
from decorators.trace_closer import TraceCloser # Needed for stacking test
from decorators.logger_decorator import FunctionLogger # Needed for stacking test
from decorators.context_vars import log_uuid_var, current_log_data

# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_logging_context():
    """
    Sets up context variables before each test and resets after.
    Simulates the context setup done by TraceCloser.
    """
    test_uuid = str(uuid.uuid4())
    test_data = {}
    token_uuid = log_uuid_var.set(test_uuid)
    token_data = current_log_data.set(test_data)
    # print(f"\n[Fixture Setup] UUID: {test_uuid}, Data: {test_data}")
    yield test_uuid, test_data # Provide uuid and data dict to the test
    # print(f"[Fixture Teardown] Resetting UUID/Data")
    log_uuid_var.reset(token_uuid)
    current_log_data.reset(token_data)


# --- Test Functions ---

# test_trace_cpu_basic remains the same

def test_trace_cpu_psutil_error_start(mocker, caplog, setup_logging_context):
    """
    Tests behavior when psutil.cpu_percent fails on the first call.
    """
    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.WARNING) # Capture WARNING messages

    # Mock psutil.cpu_percent to raise an error on the first call
    mock_cpu_percent = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    # Make the second call (in finally block) also return a value or raise an error
    # depending on what you want to test further. Here, let's make it succeed.
    mock_cpu_percent.side_effect = [RuntimeError("psutil failed"), 15.0] # Error on start, success on (attempted) end

    @TraceCpu() # Apply the decorator
    def sample_function(x):
        return x + 1

    # Call the decorated function
    result = sample_function(10)

    # --- Assertions ---
    # 1. Function behavior
    assert result == 11 # Function should still execute

    # 2. Context variable update
    assert 'cpu_delta' not in test_data # Delta should not be calculated because start failed

    # 3. Logging output
    assert "Could not get start CPU usage" in caplog.text
    # Check that the end CPU usage is attempted and logged (if DEBUG level was set)
    # Check that the final "Could not get end CPU usage *or delta*" warning is NOT present
    # because the end call itself didn't fail here.
    assert "Could not get end CPU usage or delta" not in caplog.text
    assert TraceCpu.DB_LOG_PREFIX not in caplog.text # No DB log because delta couldn't be calculated

    # 4. Mock calls
    # --- Corrected Assertion ---
    # The decorator calls cpu_percent before the try and in the finally block.
    assert mock_cpu_percent.call_count == 2 # Expect two calls even if the first fails.


# test_trace_cpu_psutil_error_end remains the same
# test_trace_cpu_no_context_uuid remains the same
# test_trace_cpu_stacked remains the same

# (Include the unchanged test functions test_trace_cpu_basic,
# test_trace_cpu_psutil_error_end, test_trace_cpu_no_context_uuid,
# and test_trace_cpu_stacked here if providing the full file)

