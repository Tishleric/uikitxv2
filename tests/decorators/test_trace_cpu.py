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
from decorators.trace_time import TraceTime # Needed for stacking test
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
    yield test_uuid, test_data
    log_uuid_var.reset(token_uuid)
    current_log_data.reset(token_data)


# --- Test Functions ---

# test_trace_cpu_basic remains the same

def test_trace_cpu_psutil_error_start(mocker, caplog, setup_logging_context):
    """
    Tests behavior when psutil.cpu_percent fails on the first call.
    """
    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.WARNING)

    mock_cpu_percent = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    mock_cpu_percent.side_effect = [RuntimeError("psutil failed"), 15.0]

    @TraceCpu()
    def sample_function(x):
        return x + 1

    result = sample_function(10)

    assert result == 11
    assert 'cpu_delta' not in test_data
    assert "Could not get start CPU usage" in caplog.text
    assert "Could not get end CPU usage or delta" not in caplog.text
    assert TraceCpu.DB_LOG_PREFIX not in caplog.text
    assert mock_cpu_percent.call_count == 2


# test_trace_cpu_psutil_error_end remains the same
# test_trace_cpu_no_context_uuid remains the same
# test_trace_cpu_stacked remains the same

# (Include the unchanged test functions test_trace_cpu_basic,
# test_trace_cpu_psutil_error_end, test_trace_cpu_no_context_uuid,
# and test_trace_cpu_stacked here if providing the full file)

