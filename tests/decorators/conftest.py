# tests/decorators/conftest.py

import pytest
import uuid
import contextvars
import psutil # Import psutil here
from unittest.mock import MagicMock, patch

# Assuming 'src' is accessible in the path for imports
from monitoring.decorators.context_vars import log_uuid_var, current_log_data

@pytest.fixture(autouse=True)
def setup_logging_context():
    """
    Sets up shared context variables (log_uuid_var, current_log_data)
    before each decorator test and resets them afterwards.
    Simulates the context setup potentially done by TraceCloser or needed
    by other decorators.

    Yields:
        tuple: The generated test UUID (str) and the initial data dictionary (dict).
    """
    test_uuid = str(uuid.uuid4())
    test_data = {} # Start with an empty dict for each test
    token_uuid = None
    token_data = None
    try:
        # Set the context variables for the test
        token_uuid = log_uuid_var.set(test_uuid)
        token_data = current_log_data.set(test_data)
        # print(f"\n[Fixture Setup] Context Set - UUID: {test_uuid}, Data: {test_data}")
        yield test_uuid, test_data # Provide uuid and data dict to the test
    finally:
        # Reset the context variables after the test runs
        # print(f"[Fixture Teardown] Resetting Context - UUID Token: {token_uuid}, Data Token: {token_data}")
        if token_uuid:
            try:
                log_uuid_var.reset(token_uuid)
            except ValueError: # Handle cases where context might have been reset already
                 pass
        if token_data:
            try:
                current_log_data.reset(token_data)
            except ValueError:
                 pass
        # print(f"[Fixture Teardown] Context Reset - Current UUID: {log_uuid_var.get()}, Current Data: {current_log_data.get()}")


@pytest.fixture
def mock_psutil_process(mocker):
    """
    Mocks decorators.trace_memory.CURRENT_PROCESS directly and its memory_info method.
    This avoids issues with CURRENT_PROCESS being instantiated before patching.
    """
    mock_process = MagicMock(spec=psutil.Process) # Use spec for better mocking
    mock_memory_info = MagicMock()
    # Set default return values (can be overridden in tests)
    # Simulate 100MB RSS memory initially
    mock_memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)
    mock_process.memory_info = mock_memory_info

    # --- Corrected Patch Target ---
    # Patch the CURRENT_PROCESS instance within the trace_memory module
    patcher = mocker.patch('decorators.trace_memory.CURRENT_PROCESS', mock_process)
    yield mock_process # Provide the mock process object to the test
    # Patcher stops automatically if using mocker fixture directly


@pytest.fixture
def mock_psutil_cpu(mocker):
    """Mocks psutil.cpu_percent."""
    # --- Corrected Patch Target ---
    # Patch the function directly where it's imported/used in trace_cpu
    mock_cpu = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    # Set default side effect (can be overridden in tests)
    # Simulate 10% -> 15% CPU usage
    mock_cpu.side_effect = [10.0, 15.0]
    yield mock_cpu
