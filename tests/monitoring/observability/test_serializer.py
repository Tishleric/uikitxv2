"""Tests for smart serializer - Phase 1"""

import pytest


def test_import():
    """Test that SmartSerializer can be imported"""
    from lib.monitoring.serializers import SmartSerializer
    assert SmartSerializer is not None
    
    # Can instantiate
    serializer = SmartSerializer()
    assert serializer is not None 