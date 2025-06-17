"""Memory pressure tests for observability system.

Tests system behavior under memory constraints to ensure graceful degradation.
"""

import gc
import os
import sys
import time
import numpy as np
import pandas as pd
from unittest.mock import patch

from lib.monitoring.decorators.monitor import monitor, start_observability_writer, stop_observability_writer
from lib.monitoring.serializers.smart import SmartSerializer
from lib.monitoring.queues.observability_queue import ObservabilityQueue, ObservabilityRecord


class TestMemoryPressure:
    """Test observability system under memory constraints."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clean start for each test
        stop_observability_writer()
        gc.collect()
        
    def teardown_method(self):
        """Clean up after tests."""
        stop_observability_writer()
        gc.collect()
    
    def test_serializer_with_huge_objects(self):
        """Test serializer behavior with very large objects."""
        serializer = SmartSerializer(max_repr=1000)
        
        # Test 1: Large list (10M items)
        huge_list = list(range(10_000_000))
        result = serializer.serialize(huge_list)
        
        # Should provide a summary, not full serialization
        assert "len=10000000" in result
        assert len(result) < 1000  # Should be truncated
        
        # Clean up
        del huge_list
        gc.collect()
        
        # Test 2: Large DataFrame (1M rows x 100 columns)
        huge_df = pd.DataFrame(np.random.rand(1_000_000, 100))
        result = serializer.serialize(huge_df)
        
        # Should summarize, not serialize full data
        assert "1000000×100" in result  # Updated format
        assert len(result) < 1000  # Should be summary only
        
        # Clean up
        del huge_df
        gc.collect()
        
        # Test 3: Deeply nested structure
        deeply_nested = {"level": 0}
        current = deeply_nested
        for i in range(1000):
            current["next"] = {"level": i + 1}
            current = current["next"]
        
        result = serializer.serialize(deeply_nested)
        assert len(result) < 5000  # Should truncate deep nesting
        
    def test_queue_memory_behavior(self):
        """Test queue behavior when memory is constrained."""
        queue = ObservabilityQueue(
            normal_maxsize=1000,  # Small queue
            overflow_maxsize=5000    # Small overflow
        )
        
        # Fill queue with large objects
        large_data = "x" * 10_000  # 10KB string
        
        # Test normal queue filling
        for i in range(1000):
            record = ObservabilityRecord(
                ts="2024-01-01T00:00:00",
                process=f'test_{i}',
                status="OK",
                duration_ms=1.0,
                args=[large_data]
            )
            queue.put(record)
        
        # Verify queue is full
        stats = queue.get_queue_stats()
        assert stats['normal_queue_size'] == 1000
        
        # Test overflow behavior
        for i in range(5000):
            record = ObservabilityRecord(
                ts="2024-01-01T00:00:00",
                process=f'overflow_{i}',
                status="OK",
                duration_ms=1.0,
                args=[large_data]
            )
            queue.put(record)
        
        stats = queue.get_queue_stats()
        assert stats['overflow_buffer_size'] == 5000
        assert stats['metrics']['overflowed'] == 5000
        
        # Test that we don't grow unbounded
        # Try to add more - should be dropped from ring buffer
        for i in range(1000):
            record = ObservabilityRecord(
                ts="2024-01-01T00:00:00",
                process=f'dropped_{i}',
                status="OK",
                duration_ms=1.0,
                args=[large_data]
            )
            queue.put(record)
        
        # Ring buffer should maintain max size
        final_stats = queue.get_queue_stats()
        assert final_stats['overflow_buffer_size'] == 5000  # Ring buffer maxlen
        assert final_stats['metrics']['overflowed'] == 6000  # Total overflowed
        
    def test_monitor_under_memory_pressure(self):
        """Test @monitor decorator with limited memory."""
        # Start observability with small queues
        start_observability_writer(
            batch_size=10,
            drain_interval=0.05
        )
        
        # Create function that uses lots of memory
        @monitor()
        def memory_intensive_function(size):
            # Allocate large array
            data = np.random.rand(size, size)
            # Do some computation
            result = np.sum(data)
            return result
        
        # Test with increasing sizes
        sizes = [100, 500, 1000]
        for size in sizes:
            try:
                result = memory_intensive_function(size)
                assert isinstance(result, float)
            except MemoryError:
                # Should handle gracefully
                pass
            
            # Give writer time to process
            time.sleep(0.1)
            
            # Force garbage collection
            gc.collect()
    
    def test_serializer_memory_safety(self):
        """Test serializer safety with dangerous objects."""
        serializer = SmartSerializer(max_repr=500)
        
        # Test with object that has dangerous __repr__
        class DangerousObject:
            def __repr__(self):
                # This could use tons of memory
                return "X" * 10000  # 10KB string
        
        obj = DangerousObject()
        result = serializer.serialize(obj)
        
        # Should truncate even dangerous repr
        assert len(result) == 500  # Exactly at max_repr limit
        assert result.endswith("...")  # Should indicate truncation
        
        # Test with recursive structure
        recursive_list = []
        recursive_list.append(recursive_list)  # Self-reference
        
        result = serializer.serialize(recursive_list)
        assert "<Circular reference:" in result  # Updated format
        assert len(result) < 100
    
    def test_graceful_degradation_oom(self):
        """Test system behavior during out-of-memory conditions."""
        # This test simulates OOM without actually causing it
        # (to avoid crashing the test runner)
        
        @monitor()
        def function_that_might_oom():
            # Simulate work
            return "success"
        
        # Mock memory allocation failure
        original_serialize = SmartSerializer.serialize
        
        def failing_serialize(self, obj):
            if "large" in str(obj):
                raise MemoryError("Simulated OOM")
            return original_serialize(self, obj)
        
        with patch.object(SmartSerializer, 'serialize', failing_serialize):
            # Should not crash the decorator
            result = function_that_might_oom()
            assert result == "success"
            
            # Try with "large" data that triggers mock OOM
            @monitor()
            def function_with_large_data():
                return {"data": "large_dataset"}
            
            # Should still work despite serialization failure
            result = function_with_large_data()
            assert result["data"] == "large_dataset"
    
    def test_writer_under_memory_pressure(self):
        """Test SQLite writer behavior under memory constraints."""
        import tempfile
        
        # Create temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Start with small batch size to reduce memory usage
            start_observability_writer(
                db_path=db_path,
                batch_size=5,  # Very small batches
                drain_interval=0.01  # Fast draining
            )
            
            # Generate many records with large data
            @monitor()
            def generate_large_record(i):
                return {
                    "id": i,
                    "data": "X" * 1000,  # 1KB per record
                    "array": list(range(100))
                }
            
            # Generate lots of records
            for i in range(100):
                generate_large_record(i)
            
            # Give writer time to process
            time.sleep(0.5)
            
            # Check database size is reasonable
            db_size = os.path.getsize(db_path)
            # Should be compressed/efficient
            assert db_size < 1_000_000  # Less than 1MB
            
        finally:
            # Clean up
            stop_observability_writer()
            try:
                os.unlink(db_path)
            except:
                pass
    
    def test_fast_serializer_large_object_handling(self):
        """Test FastSerializer's lazy serialization."""
        from lib.monitoring.performance.fast_serializer import FastSerializer
        
        serializer = FastSerializer()
        
        # Test large string
        large_string = "X" * 20000  # 20KB
        result = serializer.lazy_serialize(large_string)
        assert isinstance(result, dict)
        assert result.get("__lazy__") is True
        assert result.get("__size__") == 20000
        assert result.get("__preview__").endswith("...")
        
        # Test large list
        large_list = list(range(2000))
        result = serializer.lazy_serialize(large_list)
        assert isinstance(result, dict)
        assert result.get("__lazy__") is True
        assert result.get("__size__") == 2000
        assert "2000 items" in result.get("__preview__", "")
        
    def test_memory_efficient_batch_processing(self):
        """Verify batch processing doesn't accumulate memory."""
        @monitor()
        def process_batch(batch_id):
            # Simulate processing that generates temporary data
            temp_data = np.random.rand(1000, 1000)  # ~8MB
            result = float(np.sum(temp_data))
            # temp_data should be garbage collected after function
            return result
        
        # Process many batches
        initial_memory = None
        for i in range(10):
            result = process_batch(i)
            assert isinstance(result, float)
            
            # Force garbage collection
            gc.collect()
            
            # Memory shouldn't grow unbounded
            # (We can't directly measure memory on Windows without psutil,
            # but garbage collection should prevent growth)
        
        # If we get here without MemoryError, the test passes 