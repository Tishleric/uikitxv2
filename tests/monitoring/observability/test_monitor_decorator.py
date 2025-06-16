"""Tests for monitor decorator - Phase 2"""

import pytest
import time
import io
import sys
from contextlib import redirect_stdout


def test_import():
    """Test that monitor decorator can be imported"""
    from lib.monitoring.decorators import monitor
    assert monitor is not None
    assert callable(monitor)


def test_basic_decoration():
    """Test that decorator doesn't break function"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="test")
    def test_function(x, y):
        return x + y
    
    # Function should still work
    result = test_function(2, 3)
    assert result == 5
    
    # Function name should be preserved
    assert test_function.__name__ == "test_function"


def test_console_output():
    """Test that decorator prints to console"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="test.group")
    def simple_function():
        return "done"
    
    # Capture console output
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = simple_function()
    
    output = captured_output.getvalue()
    
    # Check output format
    assert "[MONITOR]" in output
    assert "test.group" in output
    assert "simple_function" in output
    assert "executed in" in output
    assert "ms" in output
    
    # Check function still returns correctly
    assert result == "done"


def test_timing_measurement():
    """Test that timing is measured accurately"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="timing.test")
    def slow_function():
        time.sleep(0.1)  # Sleep for 100ms
        return "slow"
    
    # Capture output
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = slow_function()
    
    output = captured_output.getvalue()
    
    # Extract timing from output
    # Format: "[MONITOR] timing.test.module.slow_function executed in XXX.XXXms"
    import re
    match = re.search(r'executed in (\d+\.\d+)ms', output)
    assert match is not None
    
    duration_ms = float(match.group(1))
    
    # Check timing is reasonable (should be >= 100ms, allowing for some variance)
    assert duration_ms >= 100.0
    assert duration_ms < 150.0  # Should not be too much over
    
    assert result == "slow"


def test_exception_handling():
    """Test that exceptions are handled and re-raised"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="error.test")
    def failing_function():
        raise ValueError("Test error")
    
    # Capture output
    captured_output = io.StringIO()
    
    with redirect_stdout(captured_output):
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
    
    output = captured_output.getvalue()
    
    # Check error output
    assert "[MONITOR]" in output
    assert "error.test" in output
    assert "failing_function" in output
    assert "FAILED after" in output
    assert "ms" in output
    assert "ValueError: Test error" in output


def test_function_metadata_capture():
    """Test that function metadata is captured correctly"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="metadata")
    def test_func(a, b=10):
        """Test function docstring"""
        return a + b
    
    # Check metadata preservation
    assert test_func.__name__ == "test_func"
    assert test_func.__doc__ == "Test function docstring"
    # Module name will include the full path when running tests
    assert "test_monitor_decorator" in test_func.__module__
    
    # Test function still works with default arguments
    result = test_func(5)
    assert result == 15
    
    result = test_func(5, b=20)
    assert result == 25


def test_multiple_decorations():
    """Test that multiple functions can be decorated"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="multi.test")
    def func1():
        return 1
    
    @monitor(process_group="multi.test")
    def func2():
        return 2
    
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        r1 = func1()
        r2 = func2()
    
    output = captured_output.getvalue()
    
    # Both functions should be traced
    assert "func1" in output
    assert "func2" in output
    assert output.count("[MONITOR]") == 2
    
    assert r1 == 1
    assert r2 == 2


def test_nested_function_calls():
    """Test decorator with nested function calls"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="nested")
    def inner_func(x):
        return x * 2
    
    @monitor(process_group="nested")
    def outer_func(x):
        return inner_func(x) + 1
    
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = outer_func(5)
    
    output = captured_output.getvalue()
    
    # Both functions should be traced
    assert output.count("[MONITOR]") == 2
    assert "inner_func" in output
    assert "outer_func" in output
    
    # Check execution order (inner should execute first due to call order)
    lines = output.strip().split('\n')
    assert len(lines) == 2
    assert "inner_func" in lines[0]
    assert "outer_func" in lines[1]
    
    assert result == 11  # (5 * 2) + 1 
    assert result == 5
    
    # Function name should be preserved
    assert test_function.__name__ == "test_function"


def test_console_output():
    """Test that decorator prints to console"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="test.group")
    def simple_function():
        return "done"
    
    # Capture console output
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = simple_function()
    
    output = captured_output.getvalue()
    
    # Check output format
    assert "[MONITOR]" in output
    assert "test.group" in output
    assert "simple_function" in output
    assert "executed in" in output
    assert "ms" in output
    
    # Check function still returns correctly
    assert result == "done"


def test_timing_measurement():
    """Test that timing is measured accurately"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="timing.test")
    def slow_function():
        time.sleep(0.1)  # Sleep for 100ms
        return "slow"
    
    # Capture output
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = slow_function()
    
    output = captured_output.getvalue()
    
    # Extract timing from output
    # Format: "[MONITOR] timing.test.module.slow_function executed in XXX.XXXms"
    import re
    match = re.search(r'executed in (\d+\.\d+)ms', output)
    assert match is not None
    
    duration_ms = float(match.group(1))
    
    # Check timing is reasonable (should be >= 100ms, allowing for some variance)
    assert duration_ms >= 100.0
    assert duration_ms < 150.0  # Should not be too much over
    
    assert result == "slow"


def test_exception_handling():
    """Test that exceptions are handled and re-raised"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="error.test")
    def failing_function():
        raise ValueError("Test error")
    
    # Capture output
    captured_output = io.StringIO()
    
    with redirect_stdout(captured_output):
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
    
    output = captured_output.getvalue()
    
    # Check error output
    assert "[MONITOR]" in output
    assert "error.test" in output
    assert "failing_function" in output
    assert "FAILED after" in output
    assert "ms" in output
    assert "ValueError: Test error" in output


def test_function_metadata_capture():
    """Test that function metadata is captured correctly"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="metadata")
    def test_func(a, b=10):
        """Test function docstring"""
        return a + b
    
    # Check metadata preservation
    assert test_func.__name__ == "test_func"
    assert test_func.__doc__ == "Test function docstring"
    # Module name will include the full path when running tests
    assert "test_monitor_decorator" in test_func.__module__
    
    # Test function still works with default arguments
    result = test_func(5)
    assert result == 15
    
    result = test_func(5, b=20)
    assert result == 25


def test_multiple_decorations():
    """Test that multiple functions can be decorated"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="multi.test")
    def func1():
        return 1
    
    @monitor(process_group="multi.test")
    def func2():
        return 2
    
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        r1 = func1()
        r2 = func2()
    
    output = captured_output.getvalue()
    
    # Both functions should be traced
    assert "func1" in output
    assert "func2" in output
    assert output.count("[MONITOR]") == 2
    
    assert r1 == 1
    assert r2 == 2


def test_nested_function_calls():
    """Test decorator with nested function calls"""
    from lib.monitoring.decorators import monitor
    
    @monitor(process_group="nested")
    def inner_func(x):
        return x * 2
    
    @monitor(process_group="nested")
    def outer_func(x):
        return inner_func(x) + 1
    
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        result = outer_func(5)
    
    output = captured_output.getvalue()
    
    # Both functions should be traced
    assert output.count("[MONITOR]") == 2
    assert "inner_func" in output
    assert "outer_func" in output
    
    # Check execution order (inner should execute first due to call order)
    lines = output.strip().split('\n')
    assert len(lines) == 2
    assert "inner_func" in lines[0]
    assert "outer_func" in lines[1]
    
    assert result == 11  # (5 * 2) + 1 