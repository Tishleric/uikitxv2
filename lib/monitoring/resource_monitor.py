"""Resource monitoring abstraction layer.

This module provides a clean abstraction over system resource monitoring,
decoupling the monitoring system from psutil implementation details.
"""

import os
import time
from typing import Optional, Tuple, Protocol
from dataclasses import dataclass


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    timestamp: float = 0.0


class ResourceMonitorProtocol(Protocol):
    """Protocol for resource monitoring implementations."""
    
    def is_available(self) -> bool:
        """Check if resource monitoring is available."""
        ...
    
    def get_cpu_percent(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        ...
    
    def get_memory_mb(self) -> Optional[float]:
        """Get current memory usage in MB."""
        ...
    
    def take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current resource usage."""
        ...


class PsutilMonitor:
    """Resource monitor using psutil library."""
    
    def __init__(self):
        self._available = False
        self._process = None
        self._last_cpu_time = None
        self._last_check_time = None
        
        # Lazy initialization
        self._initialize()
    
    def _initialize(self):
        """Lazy initialization of psutil resources."""
        try:
            import psutil
            self._psutil = psutil
            
            # Try to get current process
            try:
                self._process = psutil.Process(os.getpid())
                # Verify process is accessible
                self._process.cpu_percent(interval=0)
                self._available = True
            except Exception as e:
                # Handle any process-related errors
                # This catches both real psutil exceptions and mocked exceptions
                self._available = False
                self._process = None
        except ImportError:
            self._available = False
            self._psutil = None
    
    def is_available(self) -> bool:
        """Check if psutil monitoring is available."""
        return self._available
    
    def get_cpu_percent(self) -> Optional[float]:
        """Get CPU usage percentage."""
        if not self._available or not self._process:
            return None
        
        try:
            # Use interval=None for non-blocking call
            return self._process.cpu_percent(interval=None)
        except Exception:
            # Handle process termination, access issues, etc.
            self._available = False
            return None
    
    def get_memory_mb(self) -> Optional[float]:
        """Get memory usage in MB."""
        if not self._available or not self._process:
            return None
        
        try:
            mem_info = self._process.memory_info()
            return mem_info.rss / 1024 / 1024
        except Exception:
            self._available = False
            return None
    
    def take_snapshot(self) -> ResourceSnapshot:
        """Take a resource snapshot."""
        return ResourceSnapshot(
            cpu_percent=self.get_cpu_percent(),
            memory_mb=self.get_memory_mb(),
            timestamp=time.time()
        )


class NullMonitor:
    """Null implementation when monitoring is not available."""
    
    def is_available(self) -> bool:
        return False
    
    def get_cpu_percent(self) -> Optional[float]:
        return None
    
    def get_memory_mb(self) -> Optional[float]:
        return None
    
    def take_snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(timestamp=time.time())


class MockMonitor:
    """Mock implementation for testing."""
    
    def __init__(self, cpu_percent: float = 25.0, memory_mb: float = 100.0):
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.call_count = {"cpu": 0, "memory": 0}
    
    def is_available(self) -> bool:
        return True
    
    def get_cpu_percent(self) -> Optional[float]:
        self.call_count["cpu"] += 1
        return self.cpu_percent
    
    def get_memory_mb(self) -> Optional[float]:
        self.call_count["memory"] += 1
        return self.memory_mb
    
    def take_snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(
            cpu_percent=self.get_cpu_percent(),
            memory_mb=self.get_memory_mb(),
            timestamp=time.time()
        )


class ResourceMonitor:
    """Main resource monitor with graceful degradation."""
    
    def __init__(self, backend: Optional[ResourceMonitorProtocol] = None):
        """Initialize with specified backend or auto-detect."""
        if backend is not None:
            self._backend = backend
        else:
            # Try psutil first, fall back to null
            psutil_monitor = PsutilMonitor()
            if psutil_monitor.is_available():
                self._backend = psutil_monitor
            else:
                self._backend = NullMonitor()
    
    @property
    def backend(self) -> ResourceMonitorProtocol:
        """Get the current backend."""
        return self._backend
    
    def is_available(self) -> bool:
        """Check if resource monitoring is available."""
        return self._backend.is_available()
    
    def measure_resources(self, start_snapshot: Optional[ResourceSnapshot] = None) -> Tuple[Optional[float], Optional[float]]:
        """Measure resource changes from a start snapshot.
        
        Returns:
            Tuple of (cpu_delta, memory_delta_mb) or (None, None) if not available
        """
        if not self.is_available():
            return None, None
        
        if start_snapshot is None:
            # No baseline, just return current values
            snapshot = self._backend.take_snapshot()
            return snapshot.cpu_percent, snapshot.memory_mb
        
        # Calculate deltas
        end_snapshot = self._backend.take_snapshot()
        
        cpu_delta = None
        if start_snapshot.cpu_percent is not None and end_snapshot.cpu_percent is not None:
            cpu_delta = end_snapshot.cpu_percent - start_snapshot.cpu_percent
        
        memory_delta = None
        if start_snapshot.memory_mb is not None and end_snapshot.memory_mb is not None:
            memory_delta = end_snapshot.memory_mb - start_snapshot.memory_mb
        
        return cpu_delta, memory_delta
    
    def take_snapshot(self) -> ResourceSnapshot:
        """Take a resource snapshot."""
        return self._backend.take_snapshot()


# Global singleton instance
_global_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get the global resource monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor


def set_resource_monitor(monitor: ResourceMonitor) -> None:
    """Set the global resource monitor (mainly for testing)."""
    global _global_monitor
    _global_monitor = monitor 