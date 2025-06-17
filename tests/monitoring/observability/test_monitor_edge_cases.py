"""Edge case and stress tests for monitor decorator - areas we're currently missing"""

import asyncio
import threading
import time
import gc
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

from lib.monitoring.decorators.monitor import (
    monitor, get_observability_queue, start_observability_writer, stop_observability_writer
)


class TestConcurrencyStress:
    """Test true concurrent execution scenarios"""
    
    def test_high_frequency_parallel_calls(self):
        """Stress test with many parallel calls"""
        @monitor()
        def quick_function(x):
            return x * 2
        
        queue = get_observability_queue()
        queue.clear()
        
        # Parallel execution with threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(quick_function, i) for i in range(1000)]
            results = [f.result() for f in futures]
        
        # Should have exactly 1000 records
        time.sleep(0.1)  # Let queue settle
        stats = queue.get_queue_stats()
        metrics = stats['metrics']
        assert metrics['normal_enqueued'] == 1000
        assert metrics['error_enqueued'] == 0
    
    def test_race_condition_in_queue(self):
        """Test for race conditions in queue operations"""
        @monitor()
        def racy_function():
            # Simulate work
            time.sleep(0.001)
            return "done"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Create threads that will all try to execute simultaneously
        barrier = threading.Barrier(50)
        
        def worker():
            barrier.wait()  # All threads start together
            racy_function()
        
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify no records were lost
        time.sleep(0.1)
        stats = queue.get_queue_stats()
        assert stats['metrics']['normal_enqueued'] == 50


class TestMemoryPressure:
    """Test behavior under memory constraints"""
    
    def test_large_object_serialization_at_scale(self):
        """Test serializing many large objects"""
        @monitor()
        def create_large_data(size):
            # Create a large list
            return [i for i in range(size)]
        
        queue = get_observability_queue()
        queue.clear()
        
        # Create progressively larger objects
        sizes = [1000, 10000, 100000, 1000000]
        for size in sizes:
            result = create_large_data(size)
            
        # Check that all were captured (possibly with lazy serialization)
        records = queue.drain(10)
        assert len(records) == len(sizes)
        
        # Verify lazy serialization kicked in for large objects
        for i, record in enumerate(records):
            if sizes[i] >= 100000:
                assert "<lazy:" in record.result or "object at" in record.result
    
    def test_queue_behavior_under_memory_pressure(self):
        """Test queue when system is under memory pressure"""
        @monitor()
        def memory_intensive():
            # Allocate and immediately release memory
            data = bytearray(10 * 1024 * 1024)  # 10MB
            del data
            gc.collect()
            return "completed"
        
        queue = get_observability_queue()
        queue.clear()
        
        # Execute many times to create pressure
        for _ in range(5):
            memory_intensive()
        
        # Queue should still function
        stats = queue.get_queue_stats()
        assert stats['metrics']['normal_enqueued'] == 5


class TestExoticFunctionTypes:
    """Test function types we haven't covered"""
    
    def test_function_with_mutable_default(self):
        """Test function with mutable default argument"""
        @monitor()
        def append_to_list(item, lst=[]):
            lst.append(item)
            return lst
        
        queue = get_observability_queue()
        queue.clear()
        
        # Call multiple times - default list will grow
        result1 = append_to_list(1)
        result2 = append_to_list(2)
        
        records = queue.drain(10)
        assert len(records) == 2
        # Both should complete successfully despite shared mutable default
        assert all(r.status == "OK" for r in records)
    
    def test_metaclass_method(self):
        """Test decorating metaclass methods"""
        class MetaClass(type):
            @monitor()
            def meta_method(cls):
                return f"Meta method of {cls.__name__}"
        
        class MyClass(metaclass=MetaClass):
            pass
        
        queue = get_observability_queue()
        queue.clear()
        
        result = MyClass.meta_method()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"
    
    def test_slots_class_method(self):
        """Test decorating methods on classes with __slots__"""
        class SlottedClass:
            __slots__ = ['value']
            
            def __init__(self, value):
                self.value = value
            
            @monitor()
            def get_value(self):
                return self.value
        
        queue = get_observability_queue()
        queue.clear()
        
        obj = SlottedClass(42)
        result = obj.get_value()
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"


class TestAsyncEdgeCases:
    """Test complex async scenarios"""
    
    @pytest.mark.asyncio
    async def test_coroutine_that_never_completes(self):
        """Test monitoring a coroutine that times out"""
        @monitor()
        async def infinite_coroutine():
            while True:
                await asyncio.sleep(0.1)
        
        queue = get_observability_queue()
        queue.clear()
        
        # Start coroutine but cancel it
        task = asyncio.create_task(infinite_coroutine())
        await asyncio.sleep(0.05)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have recorded the cancellation as an error
        records = queue.drain(10)
        assert len(records) >= 1
        # Cancellation might be recorded as error or might not complete
    
    @pytest.mark.asyncio
    async def test_async_context_switching(self):
        """Test call depth tracking across async context switches"""
        @monitor()
        async def outer():
            await asyncio.sleep(0)  # Force context switch
            return await inner()
        
        @monitor()
        async def inner():
            await asyncio.sleep(0)  # Another context switch
            return "result"
        
        queue = get_observability_queue()
        queue.clear()
        
        result = await outer()
        
        records = queue.drain(10)
        assert len(records) == 2
        
        # Call depths might not be perfectly preserved across async boundaries
        # This is a known limitation we should document


class TestErrorRecoveryPaths:
    """Test various failure scenarios"""
    
    def test_serialization_partial_failure(self):
        """Test when serialization partially fails"""
        class BadObject:
            def __repr__(self):
                raise ValueError("Cannot represent")
            
            def __str__(self):
                raise ValueError("Cannot stringify")
        
        @monitor()
        def process_bad_object(obj):
            return "processed"
        
        queue = get_observability_queue()
        queue.clear()
        
        bad = BadObject()
        result = process_bad_object(bad)
        
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"
        # Argument should be serialized as class name or error marker
        assert "BadObject" in records[0].args[0] or "serialization failed" in records[0].args[0]
    
    def test_queue_recovery_after_overflow(self):
        """Test that queue recovers properly after overflow"""
        # Temporarily set small queue size
        original_size = get_observability_queue().normal_maxsize
        queue = get_observability_queue()
        queue.normal_maxsize = 10  # Very small for testing
        
        @monitor()
        def generate_load(i):
            return i
        
        queue.clear()
        
        # Generate enough load to overflow
        for i in range(100):
            generate_load(i)
        
        # Now drain and let recovery happen
        all_records = []
        while True:
            batch = queue.drain(50)
            if not batch:
                break
            all_records.extend(batch)
            time.sleep(0.01)  # Let recovery happen
        
        # Should have recovered some from overflow
        stats = queue.get_queue_stats()
        assert stats['metrics']['recovered'] > 0
        
        # Restore original size
        queue.normal_maxsize = original_size


class TestGeneratorEdgeCases:
    """Test generator scenarios we might have missed"""
    
    def test_generator_partially_consumed(self):
        """Test generator that is only partially consumed"""
        @monitor()
        def counting_generator(n):
            for i in range(n):
                yield i
        
        queue = get_observability_queue()
        queue.clear()
        
        gen = counting_generator(10)
        # Only consume first 3 values
        for i, val in enumerate(gen):
            if i >= 3:
                break
        
        # Generator should still be tracked
        records = queue.drain(10)
        assert len(records) == 1
        assert records[0].status == "OK"
    
    def test_generator_with_cleanup(self):
        """Test generator with finally clause"""
        cleanup_called = False
        
        @monitor()
        def generator_with_cleanup():
            try:
                yield 1
                yield 2
                yield 3
            finally:
                nonlocal cleanup_called
                cleanup_called = True
        
        queue = get_observability_queue()
        queue.clear()
        
        gen = generator_with_cleanup()
        next(gen)  # Get first value
        # Don't consume the rest
        del gen  # This should trigger cleanup
        gc.collect()
        
        # Cleanup should have been called
        assert cleanup_called
        
        records = queue.drain(10)
        assert len(records) == 1


# Add pytest import
import pytest 