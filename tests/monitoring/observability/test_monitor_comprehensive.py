"""Comprehensive test suite for enhanced @monitor decorator with Track Everything philosophy"""

import os
import time
import threading
import asyncio
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer,
    get_observability_queue
)
from lib.monitoring.queues import ObservabilityRecord
from lib.monitoring.writers import SQLiteWriter
from lib.monitoring.resource_monitor import (
    set_resource_monitor, get_resource_monitor, ResourceMonitor, NullMonitor, MockMonitor
)


class TestProcessGroups:
    """Test process group auto-derivation and explicit assignment"""
    
    def test_auto_derived_process_group(self):
        """Process group should auto-derive from module name"""
        @monitor()
        def test_function():
            return "result"
        
        # Execute and capture
        queue = get_observability_queue()
        queue.clear()
        
        result = test_function()
        
        # Check the record
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        # Process should be module_name.function_name
        assert record.process.endswith(".test_function")
        assert "test_monitor_comprehensive" in record.process
    
    def test_explicit_process_group(self):
        """Explicit process group should override auto-derivation"""
        @monitor(process_group="trading.critical")
        def test_function():
            return "result"
        
        queue = get_observability_queue()
        queue.clear()
        
        result = test_function()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].process == "trading.critical.test_function"
    
    def test_nested_process_groups(self):
        """Process groups can have multiple levels"""
        @monitor(process_group="trading.risk.calculations")
        def calculate_var():
            return 0.05
        
        queue = get_observability_queue()
        queue.clear()
        
        result = calculate_var()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].process == "trading.risk.calculations.calculate_var"


class TestCPUMemoryTracking:
    """Test CPU and memory tracking edge cases"""
    
    def test_cpu_memory_disabled_by_default_when_psutil_missing(self):
        """Without psutil, CPU/memory should be None even with capture enabled"""
        # Use NullMonitor to simulate psutil being unavailable
        original_monitor = get_resource_monitor()
        test_monitor = ResourceMonitor(backend=NullMonitor())
        
        try:
            set_resource_monitor(test_monitor)
            
            @monitor(capture={"cpu_usage": True, "memory_usage": True})
            def test_function():
                # Allocate some memory
                data = [i for i in range(1000000)]
                time.sleep(0.1)
                return len(data)
            
            queue = get_observability_queue()
            queue.clear()
            
            result = test_function()
            
            records = queue.drain(10)
            assert len(records) == 1
            record = records[0]
            
            # Should be None when psutil unavailable
            assert record.cpu_delta is None
            assert record.memory_delta_mb is None
        finally:
            set_resource_monitor(original_monitor)
    
    def test_cpu_memory_tracking_with_psutil(self):
        """With psutil, CPU/memory should be captured by default"""
        # Skip if resource monitoring is not available
        if not get_resource_monitor().is_available():
            pytest.skip("Resource monitoring not available")
        
        @monitor()  # Default captures everything
        def cpu_intensive_function():
            # Do some CPU work
            total = 0
            for i in range(1000000):
                total += i ** 2
            return total
        
        queue = get_observability_queue()
        queue.clear()
        
        result = cpu_intensive_function()
        
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        # Should have CPU/memory values (may be 0 or negative)
        assert record.cpu_delta is not None
        assert record.memory_delta_mb is not None
    
    def test_selective_capture_disabling(self):
        """Test disabling specific captures"""
        @monitor(capture={"args": False, "result": False, "cpu_usage": False, "memory_usage": False})
        def test_function(secret_arg):
            return "secret_result"
        
        queue = get_observability_queue()
        queue.clear()
        
        result = test_function("password123")
        
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        # All captures should be disabled
        assert record.args is None
        assert record.result is None
        assert record.cpu_delta is None
        assert record.memory_delta_mb is None
        
        # But basic info should still be there
        assert record.duration_ms > 0
        assert record.status == "OK"


class TestEdgeCases:
    """Test various edge cases and boundary conditions"""
    
    def test_empty_function(self):
        """Empty function should still be tracked"""
        @monitor()
        def empty_function():
            pass
        
        queue = get_observability_queue()
        queue.clear()
        
        result = empty_function()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"
        assert records[0].result is None  # Result is None for empty function
        assert records[0].duration_ms > 0
    
    def test_function_with_many_arguments(self):
        """Function with many arguments should handle all"""
        @monitor()
        def many_args_function(a, b, c, d, e, f=6, g=7, h=8, *args, **kwargs):
            return sum([a, b, c, d, e, f, g, h] + list(args) + list(kwargs.values()))
        
        queue = get_observability_queue()
        queue.clear()
        
        result = many_args_function(1, 2, 3, 4, 5, 9, 10, i=11, j=12)
        
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        # Should capture all arguments
        assert record.args is not None
        assert len(record.args) == 7  # 5 positional + 2 overrides (f and g)
        assert record.kwargs is not None
        assert len(record.kwargs) == 2  # i, j
    
    def test_function_raising_exception(self):
        """Exception should be captured with full traceback"""
        @monitor()
        def failing_function():
            raise ValueError("Test error with special chars: <>&\"'")
        
        queue = get_observability_queue()
        queue.clear()
        
        with pytest.raises(ValueError):
            failing_function()
        
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        assert record.status == "ERR"
        assert record.exception is not None
        assert "ValueError: Test error with special chars" in record.exception
        assert "Traceback" in record.exception
        assert record.duration_ms > 0  # Still tracks duration
    
    def test_recursive_function(self):
        """Recursive functions should create multiple records"""
        @monitor()
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        queue = get_observability_queue()
        queue.clear()
        
        result = fibonacci(5)  # Will create multiple records
        
        records = queue.drain(100)
        # fib(5) creates 15 calls total
        assert len(records) == 15
        
        # All should be OK
        assert all(r.status == "OK" for r in records)
        
        # Check call depths vary
        depths = set(r.call_depth for r in records)
        assert len(depths) > 1  # Multiple recursion levels
    
    def test_generator_exhaustion(self):
        """Generators should be tracked even when exhausted"""
        @monitor()
        def counting_generator(n):
            for i in range(n):
                yield i
        
        queue = get_observability_queue()
        queue.clear()
        
        gen = counting_generator(3)
        values = list(gen)  # Exhaust the generator
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"
        assert values == [0, 1, 2]
    
    def test_concurrent_execution(self):
        """Concurrent executions should be tracked separately"""
        @monitor()
        def concurrent_function(thread_id):
            time.sleep(0.01)  # Ensure some overlap
            return f"Thread {thread_id}"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Run multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=concurrent_function, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        records = queue.drain(10)
        assert len(records) == 5
        
        # Each should have different thread_id
        thread_ids = set(r.thread_id for r in records)
        assert len(thread_ids) == 5
    
    def test_very_large_arguments(self):
        """Very large arguments should be handled with lazy serialization"""
        @monitor()
        def process_large_data(data):
            return len(data)
        
        queue = get_observability_queue()
        queue.clear()
        
        # Create large data
        large_list = list(range(100000))  # 100k items
        result = process_large_data(large_list)
        
        records = queue.drain(10)
        assert len(records) == 1
        record = records[0]
        
        # Should use lazy serialization
        assert record.args is not None
        # Check that it's been truncated/lazy serialized
        serialized_arg = str(record.args[0])
        assert "LazySerializedValue" in serialized_arg or len(serialized_arg) < 20000


class TestSamplingRate:
    """Test sampling rate functionality"""
    
    def test_sampling_rate_zero(self):
        """Sampling rate 0 should never track"""
        @monitor(sample_rate=0.0)
        def never_tracked():
            return "ignored"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Call multiple times
        for _ in range(10):
            never_tracked()
        
        records = queue.drain(20)
        assert len(records) == 0
    
    def test_sampling_rate_one(self):
        """Sampling rate 1.0 should always track (default)"""
        @monitor(sample_rate=1.0)
        def always_tracked():
            return "tracked"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Call multiple times
        for _ in range(10):
            always_tracked()
        
        records = queue.drain(20)
        assert len(records) == 10
    
    def test_sampling_rate_partial(self):
        """Sampling rate 0.5 should track approximately half"""
        @monitor(sample_rate=0.5)
        def sometimes_tracked():
            return "maybe"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Call many times
        for _ in range(100):
            sometimes_tracked()
        
        records = queue.drain(200)
        # Should be approximately 50, allow for randomness
        assert 30 < len(records) < 70


class TestAsyncEdgeCases:
    """Test async-specific edge cases"""
    
    @pytest.mark.asyncio
    async def test_async_exception(self):
        """Async exceptions should be captured"""
        @monitor()
        async def async_failing():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async error")
        
        queue = get_observability_queue()
        queue.clear()
        
        with pytest.raises(RuntimeError):
            await async_failing()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "ERR"
        assert "RuntimeError: Async error" in records[0].exception
    
    @pytest.mark.asyncio
    async def test_async_generator_exception(self):
        """Async generator exceptions should be captured"""
        @monitor()
        async def async_gen_failing():
            for i in range(3):
                if i == 2:
                    raise ValueError("Async gen error")
                yield i
        
        queue = get_observability_queue()
        queue.clear()
        
        gen = async_gen_failing()
        values = []
        
        with pytest.raises(ValueError):
            async for value in gen:
                values.append(value)
        
        records = queue.drain(10)
        # We get 2 records: 1 for creation (OK), 1 for exception during iteration (ERR)
        assert len(records) == 2
        
        # First record is the exception (latest)
        assert records[0].status == "ERR"
        assert "ValueError: Async gen error" in records[0].exception
        
        # Second record is creation (earlier)
        assert records[1].status == "OK"
        
        assert values == [0, 1]  # Got first two values before error


class TestDatabaseIntegration:
    """Test full pipeline with database"""
    
    def test_full_pipeline_with_cpu_memory(self):
        """Test complete flow from decorator to database"""
        # Start writer
        db_path = "logs/test_comprehensive.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        
        queue = get_observability_queue()
        queue.clear()
        
        writer = start_observability_writer(db_path=db_path)
        
        try:
            # Create monitored function
            @monitor()
            def full_test_function(x, y):
                # Do some work
                data = [i**2 for i in range(10000)]
                return x + y + len(data)
            
            # Execute
            result = full_test_function(10, 20)
            
            # Wait for write
            time.sleep(0.5)
            
            # Query database
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check process_trace
            cursor.execute("SELECT * FROM process_trace WHERE process LIKE '%full_test_function'")
            rows = cursor.fetchall()
            assert len(rows) == 1
            
            # Verify CPU/memory columns exist and may have values
            cursor.execute("PRAGMA table_info(process_trace)")
            columns = [col[1] for col in cursor.fetchall()]
            assert "cpu_delta" in columns
            assert "memory_delta_mb" in columns
            
            conn.close()
            
        finally:
            stop_observability_writer()
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    # Run specific test class
    pytest.main([__file__, "-v", "-k", "TestProcessGroups"]) 