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
from decorators.trace_time import TraceTime # Needed for stacking test
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



def test_trace_memory_psutil_error_end(caplog, setup_logging_context, mock_psutil_process):
    """Warns and skips delta when psutil fails on the end call."""

    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.WARNING)

    mock_psutil_process.memory_info.side_effect = [
        MagicMock(rss=100 * 1024 * 1024),
        RuntimeError("psutil mem end failed"),
    ]

    @TraceMemory()
    def sample_function(x):
        return x * 2

    result = sample_function(5)

    assert result == 10
    assert "Could not get end memory usage" in caplog.text
    assert "memory_delta_mb" not in test_data
    assert mock_psutil_process.memory_info.call_count == 2


def test_trace_memory_no_psutil_process(caplog, setup_logging_context, mocker):
    """Decorator is a no-op when CURRENT_PROCESS is None."""

    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.WARNING)

    mocker.patch("decorators.trace_memory.CURRENT_PROCESS", None)

    @TraceMemory()
    def sample_function(x):
        return x - 1

    result = sample_function(4)

    assert result == 3
    assert "Could not get process handle" in caplog.text
    assert "memory_delta_mb" not in test_data


def test_trace_memory_stacked(caplog, setup_logging_context, mock_psutil_process, mock_psutil_cpu):
    """TraceMemory works correctly when stacked with other decorators."""

    test_uuid, test_data = setup_logging_context
    caplog.set_level(logging.DEBUG)

    mock_psutil_process.memory_info.side_effect = [
        MagicMock(rss=100 * 1024 * 1024),
        MagicMock(rss=110 * 1024 * 1024),
    ]
    mock_psutil_cpu.side_effect = [10.0, 12.5]

    @TraceCloser()
    @TraceMemory()
    @TraceCpu()
    @TraceTime(log_args=False, log_return=False)
    def sample_function(x):
        time.sleep(0.01)
        return x

    sample_function(7)

    assert test_data.get("memory_delta_mb") == 10.0
    assert test_data.get("cpu_delta") == 2.5
    assert "duration_s" in test_data

