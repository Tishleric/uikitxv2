"""Tests for monitor decorator - Phase 1"""

import pytest


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