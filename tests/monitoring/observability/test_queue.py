"""Tests for observability queue - Phase 1"""

import pytest


def test_import():
    """Test that ObservabilityQueue can be imported"""
    from lib.monitoring.queues import ObservabilityQueue
    assert ObservabilityQueue is not None
    
    # Can instantiate
    queue = ObservabilityQueue()
    assert queue is not None 