# tests/decorators/test_trace_closer.py

import logging
import uuid
from typing import Any

import pytest  # type: ignore[import-not-found]

from monitoring.decorators.trace_closer import TraceCloser, current_log_data, log_uuid_var  # type: ignore[import-not-found]
from monitoring.decorators.trace_cpu import TraceCpu  # type: ignore[import-not-found]
from monitoring.decorators.trace_memory import TraceMemory  # type: ignore[import-not-found]
from monitoring.decorators.trace_time import TraceTime  # type: ignore[import-not-found]

# --- Test Functions ---

def test_trace_closer_generates_uuid_if_none(caplog: pytest.LogCaptureFixture) -> None:
    """TraceCloser should create a UUID when none exists."""
    caplog.set_level(logging.INFO)
    token_uuid = log_uuid_var.set(None)
    token_data = current_log_data.set(None)

    @TraceCloser()  # type: ignore[misc]
    def func() -> str:
        return log_uuid_var.get() or ""

    generated = func()

    assert uuid.UUID(generated)  # Valid UUID
    assert log_uuid_var.get() is None
    assert current_log_data.get() is None
    assert any(record.getMessage().startswith(TraceCloser.FLOW_TRACE_PREFIX) for record in caplog.records)

    log_uuid_var.reset(token_uuid)
    current_log_data.reset(token_data)


def test_trace_closer_uses_existing_uuid(setup_logging_context: tuple[str, dict[str, Any]]) -> None:
    """TraceCloser should reuse an existing UUID."""
    test_uuid, _ = setup_logging_context

    @TraceCloser()  # type: ignore[misc]
    def func() -> str:
        return log_uuid_var.get() or ""

    result = func()

    assert result == test_uuid
    assert log_uuid_var.get() == test_uuid


def test_trace_closer_exception_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Exceptions raised inside the wrapped function are logged."""
    caplog.set_level(logging.ERROR)

    @TraceCloser()  # type: ignore[misc]
    def boom() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        boom()

    assert any("Exception in boom" in r.getMessage() for r in caplog.records)


def test_trace_closer_stacking(
    caplog: pytest.LogCaptureFixture,
    setup_logging_context: tuple[str, dict[str, Any]],
    mock_psutil_process: Any,
    mock_psutil_cpu: Any,
) -> None:
    """Metrics from stacked decorators should appear in the context."""
    test_uuid, data = setup_logging_context
    caplog.set_level(logging.INFO)

    mock_psutil_process.memory_info.side_effect = [
        type("M", (), {"rss": 100 * 1024 * 1024})(),
        type("M", (), {"rss": 104 * 1024 * 1024})(),
    ]

    mock_psutil_cpu.side_effect = [10.0, 15.0]

    @TraceCloser()  # type: ignore[misc]
    @TraceCpu()  # type: ignore[misc]
    @TraceMemory()  # type: ignore[misc]
    @TraceTime(log_args=False, log_return=False)  # type: ignore[misc]
    def work(x: int) -> int:
        return x * 2

    assert work(3) == 6
    assert data.get("duration_s") is not None
    assert data.get("cpu_delta") == 5.0
    assert data.get("memory_delta_mb") == pytest.approx(4.0, rel=0.01)
    assert any(record.getMessage().startswith(TraceCloser.FLOW_TRACE_PREFIX) for record in caplog.records)
