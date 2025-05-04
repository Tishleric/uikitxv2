# tests/decorators/test_trace_memory.py

import pytest
import logging
import json
import uuid
import time
import contextvars
import psutil # <-- Added import
from unittest.mock import patch, MagicMock

# Assuming 'src' is accessible in the path for imports
from decorators.trace_memory import TraceMemory
from decorators.trace_closer import TraceCloser # Needed for stacking test
from decorators.logger_decorator import FunctionLogger # Needed for stacking test
from decorators.trace_cpu import TraceCpu # <-- Added import
from decorators.context_vars import log_uuid_var, current_log_data

# Use the shared fixtures from tests/decorators/conftest.py
# setup_logging_context fixture is applied automatically via autouse=True
# mock_psutil_process fixture is available (now patches CURRENT_PROCESS)

# --- Test Functions ---

# test_trace_memory_basic remains the same

def test_trace_memory_psutil_error_start(caplog, setup_logging_context, mock_psutil_process):
    """
    Tests behavior when psutil memory_info fails on the first call.
    Should now correctly skip adding the context variable.
    """
    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.WARNING) # Capture WARNING messages

    # Configure mock memory_info to fail first, succeed second
    mock_psutil_process.memory_info.side_effect = [
        RuntimeError("psutil mem failed"),
        MagicMock(rss=110 * 1024 * 1024) # Success on end call
    ]

    @TraceMemory()
    def sample_function(x):
        return x + 1

    result = sample_function(10)

    # --- Assertions ---
    # 1. Function behavior
    assert result == 11 # Function should still execute

    # 2. Context variable update
    assert 'memory_delta_mb' not in test_data

    # 3. Logging output
    assert "Could not get start memory usage" in caplog.text
    assert TraceMemory.DB_LOG_PREFIX not in caplog.text # No DB log

    # 4. Mock calls
    # --- Corrected Assertion ---
    # The finally block *will* attempt the second call.
    assert mock_psutil_process.memory_info.call_count == 2


# test_trace_memory_psutil_error_end remains the same
# test_trace_memory_no_context_uuid remains the same
# test_trace_memory_no_psutil_process remains the same
# test_trace_memory_stacked remains the same

# (Include the unchanged test functions here if providing the full file)

