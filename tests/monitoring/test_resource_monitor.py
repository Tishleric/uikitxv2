"""Tests for the resource monitoring abstraction layer."""

import time
import pytest
from unittest.mock import Mock, patch

from lib.monitoring.resource_monitor import (
    ResourceSnapshot, ResourceMonitor, PsutilMonitor, 
    NullMonitor, MockMonitor, get_resource_monitor, set_resource_monitor
)


class TestResourceSnapshot:
    """Test ResourceSnapshot dataclass."""
    
    def test_creation(self):
        """Test creating resource snapshots."""
        snapshot = ResourceSnapshot(cpu_percent=25.5, memory_mb=512.3, timestamp=123.456)
        assert snapshot.cpu_percent == 25.5
        assert snapshot.memory_mb == 512.3
        assert snapshot.timestamp == 123.456
    
    def test_defaults(self):
        """Test default values."""
        snapshot = ResourceSnapshot()
        assert snapshot.cpu_percent is None
        assert snapshot.memory_mb is None
        assert snapshot.timestamp == 0.0


class TestNullMonitor:
    """Test NullMonitor implementation."""
    
    def test_always_unavailable(self):
        """Null monitor is never available."""
        monitor = NullMonitor()
        assert not monitor.is_available()
        assert monitor.get_cpu_percent() is None
        assert monitor.get_memory_mb() is None
    
    def test_snapshot_has_timestamp(self):
        """Snapshots still have timestamps."""
        monitor = NullMonitor()
        snapshot = monitor.take_snapshot()
        assert snapshot.cpu_percent is None
        assert snapshot.memory_mb is None
        assert snapshot.timestamp > 0


class TestMockMonitor:
    """Test MockMonitor for testing purposes."""
    
    def test_configurable_values(self):
        """Mock returns configured values."""
        monitor = MockMonitor(cpu_percent=42.0, memory_mb=1024.0)
        assert monitor.is_available()
        assert monitor.get_cpu_percent() == 42.0
        assert monitor.get_memory_mb() == 1024.0
    
    def test_call_counting(self):
        """Mock counts method calls."""
        monitor = MockMonitor()
        assert monitor.call_count["cpu"] == 0
        assert monitor.call_count["memory"] == 0
        
        monitor.get_cpu_percent()
        monitor.get_cpu_percent()
        monitor.get_memory_mb()
        
        assert monitor.call_count["cpu"] == 2
        assert monitor.call_count["memory"] == 1
    
    def test_snapshot(self):
        """Mock snapshots work correctly."""
        monitor = MockMonitor(cpu_percent=30.0, memory_mb=256.0)
        snapshot = monitor.take_snapshot()
        assert snapshot.cpu_percent == 30.0
        assert snapshot.memory_mb == 256.0
        assert snapshot.timestamp > 0


class TestPsutilMonitor:
    """Test PsutilMonitor implementation."""
    
    def test_without_psutil(self):
        """Test behavior when psutil is not available."""
        with patch.dict('sys.modules', {'psutil': None}):
            monitor = PsutilMonitor()
            assert not monitor.is_available()
            assert monitor.get_cpu_percent() is None
            assert monitor.get_memory_mb() is None
    
    def test_with_psutil_import_error(self):
        """Test behavior when psutil import fails."""
        # Create a PsutilMonitor subclass that overrides _initialize
        class TestPsutilMonitor(PsutilMonitor):
            def _initialize(self):
                self._available = False
                self._psutil = None
                self._process = None
        
        monitor = TestPsutilMonitor()
        assert not monitor.is_available()
    
    def test_with_process_error(self):
        """Test behavior when process access fails."""
        mock_psutil = Mock()
        mock_psutil.Process.side_effect = Exception("Access denied")
        
        with patch.dict('sys.modules', {'psutil': mock_psutil}):
            monitor = PsutilMonitor()
            assert not monitor.is_available()
    
    def test_runtime_errors_disable_monitoring(self):
        """Test that runtime errors gracefully disable monitoring."""
        mock_process = Mock()
        mock_process.cpu_percent.side_effect = Exception("Process terminated")
        
        mock_psutil = Mock()
        mock_psutil.Process.return_value = mock_process
        
        with patch.dict('sys.modules', {'psutil': mock_psutil}):
            monitor = PsutilMonitor()
            # Initially might be available
            result = monitor.get_cpu_percent()
            assert result is None
            # Should now be unavailable
            assert not monitor.is_available()


class TestResourceMonitor:
    """Test main ResourceMonitor class."""
    
    def test_auto_detection(self):
        """Test automatic backend detection."""
        # Without psutil, should use NullMonitor
        with patch('lib.monitoring.resource_monitor.PsutilMonitor') as mock_psutil_class:
            mock_psutil = Mock()
            mock_psutil.is_available.return_value = False
            mock_psutil_class.return_value = mock_psutil
            
            monitor = ResourceMonitor()
            assert isinstance(monitor.backend, NullMonitor)
    
    def test_explicit_backend(self):
        """Test using explicit backend."""
        mock_backend = MockMonitor()
        monitor = ResourceMonitor(backend=mock_backend)
        assert monitor.backend is mock_backend
        assert monitor.is_available()
    
    def test_measure_resources_unavailable(self):
        """Test measuring when monitoring is unavailable."""
        monitor = ResourceMonitor(backend=NullMonitor())
        cpu_delta, mem_delta = monitor.measure_resources()
        assert cpu_delta is None
        assert mem_delta is None
    
    def test_measure_resources_no_baseline(self):
        """Test measuring without baseline snapshot."""
        mock_backend = MockMonitor(cpu_percent=50.0, memory_mb=2048.0)
        monitor = ResourceMonitor(backend=mock_backend)
        
        cpu_delta, mem_delta = monitor.measure_resources()
        assert cpu_delta == 50.0  # Current value
        assert mem_delta == 2048.0  # Current value
    
    def test_measure_resources_with_baseline(self):
        """Test measuring with baseline snapshot."""
        mock_backend = MockMonitor(cpu_percent=30.0, memory_mb=1000.0)
        monitor = ResourceMonitor(backend=mock_backend)
        
        # Take baseline
        baseline = ResourceSnapshot(cpu_percent=20.0, memory_mb=900.0, timestamp=time.time())
        
        # Measure delta
        cpu_delta, mem_delta = monitor.measure_resources(baseline)
        assert cpu_delta == 10.0  # 30 - 20
        assert mem_delta == 100.0  # 1000 - 900
    
    def test_measure_resources_partial_data(self):
        """Test measuring with partial data available."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend.take_snapshot.return_value = ResourceSnapshot(
            cpu_percent=None,  # CPU not available
            memory_mb=500.0
        )
        
        monitor = ResourceMonitor(backend=mock_backend)
        baseline = ResourceSnapshot(cpu_percent=25.0, memory_mb=400.0)
        
        cpu_delta, mem_delta = monitor.measure_resources(baseline)
        assert cpu_delta is None  # Can't calculate delta without current value
        assert mem_delta == 100.0  # 500 - 400


class TestGlobalMonitor:
    """Test global monitor singleton."""
    
    def test_singleton_behavior(self):
        """Test that we get the same instance."""
        monitor1 = get_resource_monitor()
        monitor2 = get_resource_monitor()
        assert monitor1 is monitor2
    
    def test_set_global_monitor(self):
        """Test setting global monitor for testing."""
        original = get_resource_monitor()
        
        try:
            mock_monitor = ResourceMonitor(backend=MockMonitor())
            set_resource_monitor(mock_monitor)
            
            assert get_resource_monitor() is mock_monitor
            assert get_resource_monitor().is_available()
        finally:
            # Restore original
            set_resource_monitor(original)


class TestIntegrationWithMonitorDecorator:
    """Test integration with the monitor decorator."""
    
    def test_decorator_uses_resource_monitor(self):
        """Test that monitor decorator properly uses ResourceMonitor."""
        from lib.monitoring.decorators.monitor import monitor, get_observability_queue
        
        # Set up mock monitor
        mock_backend = MockMonitor(cpu_percent=5.0, memory_mb=100.0)
        test_monitor = ResourceMonitor(backend=mock_backend)
        original_monitor = get_resource_monitor()
        
        try:
            set_resource_monitor(test_monitor)
            
            @monitor()
            def test_function():
                time.sleep(0.01)  # Do some work
                return "result"
            
            queue = get_observability_queue()
            queue.clear()
            
            # Call function
            result = test_function()
            assert result == "result"
            
            # Check that resources were measured
            records = queue.drain(10)
            assert len(records) == 1
            
            # With MockMonitor, deltas should be 0 (same values)
            record = records[0]
            assert record.cpu_delta == 0.0  # 5.0 - 5.0
            assert record.memory_delta_mb == 0.0  # 100.0 - 100.0
            
            # Verify mock was called
            assert mock_backend.call_count["cpu"] >= 1
            assert mock_backend.call_count["memory"] >= 1
            
        finally:
            set_resource_monitor(original_monitor)
    
    def test_decorator_graceful_degradation(self):
        """Test decorator works when monitoring unavailable."""
        from lib.monitoring.decorators.monitor import monitor, get_observability_queue
        
        # Use NullMonitor (unavailable)
        test_monitor = ResourceMonitor(backend=NullMonitor())
        original_monitor = get_resource_monitor()
        
        try:
            set_resource_monitor(test_monitor)
            
            @monitor()
            def test_function(x):
                return x * 2
            
            queue = get_observability_queue()
            queue.clear()
            
            # Function should work normally
            result = test_function(21)
            assert result == 42
            
            # Check record has no resource data
            records = queue.drain(10)
            assert len(records) == 1
            record = records[0]
            assert record.cpu_delta is None
            assert record.memory_delta_mb is None
            
        finally:
            set_resource_monitor(original_monitor) 