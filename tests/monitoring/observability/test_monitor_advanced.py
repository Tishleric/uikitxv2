"""Tests for monitor decorator advanced function support - Phase 7"""

import pytest
import asyncio
import time
import sqlite3
from typing import AsyncIterator, Iterator

from lib.monitoring.decorators import monitor, start_observability_writer, stop_observability_writer, get_observability_queue
from lib.monitoring.queues import ObservabilityQueue


# Test helper to clear queue
def clear_queue():
    """Clear the observability queue for clean tests"""
    queue = get_observability_queue()
    # Drain all queues
    while not queue.error_queue.empty():
        queue.error_queue.get()
    while not queue.normal_queue.empty():
        queue.normal_queue.get()
    queue.overflow_buffer.clear()


class TestAsyncFunctions:
    """Tests for async function support"""
    
    @pytest.mark.asyncio
    async def test_async_function_basic(self):
        """Test basic async function monitoring"""
        clear_queue()
        
        @monitor(process_group="test.async")
        async def async_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        # Execute async function
        result = await async_function(5)
        assert result == 10
        
        # Check queue
        queue = get_observability_queue()
        stats = queue.get_queue_stats()
        assert stats['normal_queue_size'] > 0
        
        # Verify record details
        record = queue.normal_queue.get()
        assert record.process.endswith("async_function")
        assert record.status == "OK"
        assert record.duration_ms > 10.0  # Should take at least 10ms
        assert record.args == ["5"]
        assert record.result == "10"
    
    @pytest.mark.asyncio
    async def test_async_function_exception(self):
        """Test async function with exception"""
        clear_queue()
        
        @monitor(process_group="test.async.error")
        async def async_failing():
            await asyncio.sleep(0.01)
            raise ValueError("Async error")
        
        # Should raise exception
        with pytest.raises(ValueError, match="Async error"):
            await async_failing()
        
        # Check error was captured
        queue = get_observability_queue()
        stats = queue.get_queue_stats()
        assert stats['error_queue_size'] > 0
        
        record = queue.error_queue.get()
        assert record.status == "ERR"
        assert "ValueError: Async error" in record.exception
    
    @pytest.mark.asyncio
    async def test_async_with_context(self):
        """Test async function with context manager"""
        clear_queue()
        
        class AsyncResource:
            async def __aenter__(self):
                await asyncio.sleep(0.01)
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await asyncio.sleep(0.01)
            
            def get_data(self):
                return "resource_data"
        
        @monitor(process_group="test.async.context")
        async def use_async_resource():
            async with AsyncResource() as resource:
                return resource.get_data()
        
        result = await use_async_resource()
        assert result == "resource_data"
        
        # Verify monitoring worked
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.status == "OK"
        assert record.result == "'resource_data'"
    
    @pytest.mark.asyncio
    async def test_concurrent_async_functions(self):
        """Test multiple async functions running concurrently"""
        clear_queue()
        
        @monitor(process_group="test.async.concurrent")
        async def async_task(task_id: int, delay: float):
            await asyncio.sleep(delay)
            return f"task_{task_id}_done"
        
        # Run multiple tasks concurrently
        tasks = [
            async_task(1, 0.01),
            async_task(2, 0.02),
            async_task(3, 0.01)
        ]
        
        results = await asyncio.gather(*tasks)
        assert results == ["task_1_done", "task_2_done", "task_3_done"]
        
        # Check all were monitored
        queue = get_observability_queue()
        stats = queue.get_queue_stats()
        assert stats['normal_queue_size'] >= 3


class TestGenerators:
    """Tests for generator function support"""
    
    def test_generator_basic(self):
        """Test basic generator monitoring"""
        clear_queue()
        
        @monitor(process_group="test.generator")
        def count_generator(n: int) -> Iterator[int]:
            """Generate numbers from 0 to n-1"""
            for i in range(n):
                yield i
        
        # Create generator
        gen = count_generator(3)
        
        # Get first value (this is when we want to capture timing)
        first = next(gen)
        assert first == 0
        
        # Continue consuming generator
        assert next(gen) == 1
        assert next(gen) == 2
        
        with pytest.raises(StopIteration):
            next(gen)
        
        # Check monitoring - should capture up to first yield
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.process.endswith("count_generator")
        assert record.status == "OK"
        assert record.args == ["3"]
        # Generator monitoring captures the generator object, not individual yields
        assert "<generator at" in record.result
    
    def test_generator_with_return(self):
        """Test generator with return value"""
        clear_queue()
        
        @monitor(process_group="test.generator.return")
        def generator_with_return(items: list):
            total = 0
            for item in items:
                total += item
                yield item * 2
            return total  # This return value is accessible via StopIteration
        
        gen = generator_with_return([1, 2, 3])
        
        # Consume generator
        results = list(gen)
        assert results == [2, 4, 6]
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.status == "OK"
        assert "<generator at" in record.result
    
    def test_generator_exception(self):
        """Test generator that raises exception"""
        clear_queue()
        
        @monitor(process_group="test.generator.error")
        def failing_generator():
            yield 1
            raise ValueError("Generator error")
            yield 2  # Never reached
        
        gen = failing_generator()
        
        # First yield should work
        assert next(gen) == 1
        
        # Second should raise
        with pytest.raises(ValueError, match="Generator error"):
            next(gen)
        
        # Initial creation should be monitored as OK
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.status == "OK"  # Generator creation succeeded
    
    @pytest.mark.asyncio
    async def test_async_generator(self):
        """Test async generator monitoring"""
        clear_queue()
        
        @monitor(process_group="test.async.generator")
        async def async_count_generator(n: int) -> AsyncIterator[int]:
            for i in range(n):
                await asyncio.sleep(0.01)
                yield i
        
        # Create and consume async generator
        gen = async_count_generator(2)
        
        results = []
        async for value in gen:
            results.append(value)
        
        assert results == [0, 1]
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.process.endswith("async_count_generator")
        assert record.status == "OK"
        assert "<async_generator at" in record.result


class TestClassMethods:
    """Tests for class method support"""
    
    def test_instance_method(self):
        """Test monitoring instance methods"""
        clear_queue()
        
        class DataService:
            def __init__(self, name: str):
                self.name = name
            
            @monitor(process_group="test.class.instance")
            def process_data(self, data: str) -> str:
                return f"{self.name}: {data.upper()}"
        
        service = DataService("service1")
        result = service.process_data("hello")
        assert result == "service1: HELLO"
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.process.endswith("process_data")
        assert record.status == "OK"
        # Note: 'self' is captured as first argument
        assert len(record.args) == 2  # self and data
        assert record.args[1] == "'hello'"
        assert record.result == "'service1: HELLO'"
    
    def test_class_method(self):
        """Test monitoring @classmethod"""
        clear_queue()
        
        class ConfigService:
            default_config = {"timeout": 30}
            
            @monitor(process_group="test.class.classmethod")
            @classmethod
            def get_config(cls, key: str):
                return cls.default_config.get(key)
        
        result = ConfigService.get_config("timeout")
        assert result == 30
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.process.endswith("get_config")
        assert record.status == "OK"
        # cls is captured as first argument
        assert len(record.args) == 2
        assert record.args[1] == "'timeout'"
        assert record.result == "30"
    
    def test_static_method(self):
        """Test monitoring @staticmethod"""
        clear_queue()
        
        class MathUtils:
            @monitor(process_group="test.class.static")
            @staticmethod
            def calculate_sum(a: int, b: int) -> int:
                return a + b
        
        result = MathUtils.calculate_sum(5, 3)
        assert result == 8
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.process.endswith("calculate_sum")
        assert record.status == "OK"
        assert record.args == ["5", "3"]
        assert record.result == "8"
    
    def test_property_decorator(self):
        """Test that @property is handled gracefully"""
        clear_queue()
        
        class DataModel:
            def __init__(self, value: int):
                self._value = value
            
            @property
            @monitor(process_group="test.class.property")
            def value(self):
                return self._value * 2
        
        model = DataModel(10)
        # Property access should work even if monitoring might not be perfect
        result = model.value
        assert result == 20
    
    def test_class_method_inheritance(self):
        """Test monitoring with inheritance"""
        clear_queue()
        
        class BaseService:
            @monitor(process_group="test.class.inheritance")
            def process(self, data: str):
                return f"base: {data}"
        
        class DerivedService(BaseService):
            @monitor(process_group="test.class.inheritance")
            def process(self, data: str):
                base_result = super().process(data)
                return f"derived: {base_result}"
        
        service = DerivedService()
        result = service.process("test")
        assert result == "derived: base: test"
        
        # Should have monitored both calls
        queue = get_observability_queue()
        stats = queue.get_queue_stats()
        assert stats['normal_queue_size'] >= 2


class TestEdgeCases:
    """Test edge cases and combinations"""
    
    @pytest.mark.asyncio
    async def test_async_generator_in_class(self):
        """Test async generator as class method"""
        clear_queue()
        
        class DataStream:
            @monitor(process_group="test.edge.async_gen_class")
            async def stream_data(self, count: int):
                for i in range(count):
                    await asyncio.sleep(0.01)
                    yield f"data_{i}"
        
        stream = DataStream()
        gen = stream.stream_data(2)
        
        results = []
        async for item in gen:
            results.append(item)
        
        assert results == ["data_0", "data_1"]
        
        # Check monitoring
        queue = get_observability_queue()
        record = queue.normal_queue.get()
        assert record.status == "OK"
    
    def test_decorated_order_matters(self):
        """Test that decorator order matters for class methods"""
        clear_queue()
        
        class Service:
            # Correct order: @monitor should be closest to function
            @classmethod
            @monitor(process_group="test.edge.order")
            def correct_order(cls):
                return "correct"
            
            # This might not work as expected if monitor is outer
            @monitor(process_group="test.edge.order")
            @classmethod
            def wrong_order(cls):
                return "wrong"
        
        # Both should work, but let's verify
        result1 = Service.correct_order()
        assert result1 == "correct"
        
        result2 = Service.wrong_order()
        assert result2 == "wrong"
        
        # Check both were monitored
        queue = get_observability_queue()
        stats = queue.get_queue_stats()
        assert stats['normal_queue_size'] >= 2 