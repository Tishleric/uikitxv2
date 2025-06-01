# tests/decorators/test_trace_cpu.py

import logging
import uuid

import pytest

from monitoring.decorators.context_vars import current_log_data, log_uuid_var
from monitoring.decorators.trace_closer import TraceCloser
from monitoring.decorators.trace_cpu import TraceCpu
from monitoring.decorators.trace_time import TraceTime

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

    # 4. Mock calls
    # --- Corrected Assertion ---
    # The decorator calls cpu_percent before the try and in the finally block.
    assert mock_cpu_percent.call_count == 2 # Expect two calls even if the first fails.


def test_trace_cpu_psutil_error_end(mocker, caplog, setup_logging_context):
    """CPU delta not recorded if psutil fails on end measurement."""
    _, test_data = setup_logging_context
    caplog.set_level(logging.WARNING)

    mock_cpu = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    mock_cpu.side_effect = [10.0, RuntimeError('psutil failed')]

    @TraceCpu()
    def sample(x: int) -> int:
        return x + 1

    assert sample(3) == 4
    assert 'cpu_delta' not in test_data
    assert 'Could not get end CPU usage or calculate delta' in caplog.text
    assert mock_cpu.call_count == 2


def test_trace_cpu_no_context_uuid(mocker, caplog, setup_logging_context):
    """Decorator works when no UUID is present in context."""
    _, test_data = setup_logging_context
    caplog.set_level(logging.DEBUG)

    log_uuid_var.set(None)
    mock_cpu = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    mock_cpu.side_effect = [10.0, 15.0]

    @TraceCpu()
    def mul(x: int) -> int:
        return x * 2

    assert mul(2) == 4
    assert test_data.get('cpu_delta') == 5.0
    assert 'NO_UUID' in caplog.text
    assert mock_cpu.call_count == 2


def test_trace_cpu_stacked(mocker, caplog, setup_logging_context):
    """TraceCpu stacks with TraceTime and TraceCloser."""
    _, test_data = setup_logging_context
    caplog.set_level(logging.INFO)

    mock_cpu = mocker.patch('decorators.trace_cpu.psutil.cpu_percent')
    mock_cpu.side_effect = [10.0, 15.0]

    @TraceCloser()
    @TraceCpu()
    @TraceTime(log_args=False, log_return=False)
    def work() -> str:
        return 'ok'

    assert work() == 'ok'
    assert 'cpu_delta' in test_data
    assert 'duration_s' in test_data
    assert any('FLOW_TRACE:' in r.getMessage() for r in caplog.records)
    assert mock_cpu.call_count == 2



