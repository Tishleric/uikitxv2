"""Deep investigation into async generator exception handling behavior.

This test file aims to understand why we receive 3 records instead of 2
when an async generator raises an exception during iteration.
"""

import asyncio
import sys
import traceback
from typing import List, Any

from lib.monitoring.decorators.monitor import monitor, get_observability_queue
from lib.monitoring.queues import ObservabilityRecord


class RecordCapture:
    """Helper to capture and analyze records with detailed logging."""
    
    def __init__(self):
        self.records: List[ObservabilityRecord] = []
        self.events: List[str] = []
    
    def log_event(self, event: str):
        """Log an event with current stack depth."""
        stack_depth = len(traceback.extract_stack())
        self.events.append(f"[Depth {stack_depth}] {event}")
        print(f"EVENT: {event}")
    
    def capture_records(self) -> List[ObservabilityRecord]:
        """Capture all records from queue."""
        queue = get_observability_queue()
        self.records = queue.drain(100)
        return self.records
    
    def analyze(self):
        """Analyze captured records and events."""
        print("\n=== ANALYSIS ===")
        print(f"Total events: {len(self.events)}")
        print(f"Total records: {len(self.records)}")
        
        print("\n--- Events ---")
        for event in self.events:
            print(event)
        
        print("\n--- Records ---")
        for i, record in enumerate(self.records):
            print(f"\nRecord {i+1}:")
            print(f"  Process: {record.process}")
            print(f"  Status: {record.status}")
            print(f"  Thread ID: {record.thread_id}")
            print(f"  Call Depth: {record.call_depth}")
            if record.exception:
                print(f"  Exception: {record.exception.split(chr(10))[0]}")  # First line only


async def test_basic_async_generator():
    """Test 1: Understand basic async generator behavior without exceptions."""
    print("\n=== TEST 1: Basic Async Generator ===")
    capture = RecordCapture()
    queue = get_observability_queue()
    queue.clear()
    
    @monitor()
    async def simple_async_gen():
        capture.log_event("simple_async_gen: Starting")
        for i in range(3):
            capture.log_event(f"simple_async_gen: About to yield {i}")
            yield i
            capture.log_event(f"simple_async_gen: Resumed after yielding {i}")
        capture.log_event("simple_async_gen: Completing normally")
    
    # Create and iterate
    capture.log_event("Main: Creating generator")
    gen = simple_async_gen()
    
    capture.log_event("Main: Starting iteration")
    values = []
    async for value in gen:
        capture.log_event(f"Main: Received {value}")
        values.append(value)
    capture.log_event("Main: Iteration complete")
    
    # Analyze
    records = capture.capture_records()
    capture.analyze()
    
    assert values == [0, 1, 2]
    assert len(records) == 1  # Should be just one record for the whole generator


async def test_async_generator_with_exception_in_iteration():
    """Test 2: Exception raised during iteration (in yield)."""
    print("\n\n=== TEST 2: Exception During Iteration ===")
    capture = RecordCapture()
    queue = get_observability_queue()
    queue.clear()
    
    @monitor()
    async def exception_during_iteration():
        capture.log_event("exception_during_iteration: Starting")
        for i in range(5):
            capture.log_event(f"exception_during_iteration: About to yield {i}")
            if i == 2:
                capture.log_event("exception_during_iteration: About to raise!")
                raise ValueError(f"Error at {i}")
            yield i
            capture.log_event(f"exception_during_iteration: Resumed after yielding {i}")
    
    # Create and iterate with exception handling
    capture.log_event("Main: Creating generator")
    gen = exception_during_iteration()
    
    capture.log_event("Main: Starting iteration")
    values = []
    try:
        async for value in gen:
            capture.log_event(f"Main: Received {value}")
            values.append(value)
    except ValueError as e:
        capture.log_event(f"Main: Caught exception: {e}")
    
    capture.log_event("Main: After exception handling")
    
    # Analyze
    records = capture.capture_records()
    capture.analyze()
    
    assert values == [0, 1]  # Got first two values before exception
    print(f"\nRecord count: {len(records)}")  # This is where we see the mystery!


async def test_async_generator_wrapper_details():
    """Test 3: Detailed look at async generator wrapper behavior."""
    print("\n\n=== TEST 3: Wrapper Behavior Details ===")
    capture = RecordCapture()
    queue = get_observability_queue()
    queue.clear()
    
    @monitor()
    async def detailed_async_gen():
        """Generator with detailed logging at each step."""
        capture.log_event("detailed_async_gen: __aiter__ would be called here")
        try:
            capture.log_event("detailed_async_gen: Generator starting")
            yield 1
            capture.log_event("detailed_async_gen: After first yield")
            yield 2
            capture.log_event("detailed_async_gen: After second yield")
            raise ValueError("Intentional error")
        except Exception as e:
            capture.log_event(f"detailed_async_gen: Exception in generator: {e}")
            raise
        finally:
            capture.log_event("detailed_async_gen: Finally block")
    
    # Manual iteration to see each step
    capture.log_event("Main: Creating generator")
    gen = detailed_async_gen()
    
    capture.log_event("Main: Getting async iterator")
    agen = gen.__aiter__()
    
    values = []
    try:
        capture.log_event("Main: First __anext__")
        value = await agen.__anext__()
        values.append(value)
        capture.log_event(f"Main: Got {value}")
        
        capture.log_event("Main: Second __anext__")
        value = await agen.__anext__()
        values.append(value)
        capture.log_event(f"Main: Got {value}")
        
        capture.log_event("Main: Third __anext__ (will raise)")
        value = await agen.__anext__()  # This should raise
        values.append(value)
    except ValueError as e:
        capture.log_event(f"Main: Caught ValueError: {e}")
    except StopAsyncIteration:
        capture.log_event("Main: Got StopAsyncIteration")
    
    # Try to understand generator state after exception
    capture.log_event("Main: Checking generator state after exception")
    try:
        # Try another __anext__ to see what happens
        capture.log_event("Main: Attempting another __anext__ after exception")
        await agen.__anext__()
    except StopAsyncIteration:
        capture.log_event("Main: Generator is exhausted (StopAsyncIteration)")
    except Exception as e:
        capture.log_event(f"Main: Got different exception: {type(e).__name__}: {e}")
    
    # Analyze
    records = capture.capture_records()
    capture.analyze()
    
    # Let's examine each record in detail
    print("\n=== DETAILED RECORD EXAMINATION ===")
    for i, record in enumerate(records):
        print(f"\nRecord {i+1} Full Details:")
        print(f"  Timestamp: {record.ts}")
        print(f"  Process: {record.process}")
        print(f"  Status: {record.status}")
        print(f"  Duration: {record.duration_ms}ms")
        print(f"  Args: {record.args}")
        print(f"  Result: {record.result}")
        if record.exception:
            print("  Exception traceback:")
            for line in record.exception.split('\n')[:10]:  # First 10 lines
                print(f"    {line}")


async def test_multiple_monitor_decorators():
    """Test 4: Check if multiple @monitor decorators are somehow involved."""
    print("\n\n=== TEST 4: Multiple Decorators Check ===")
    capture = RecordCapture()
    queue = get_observability_queue()
    queue.clear()
    
    # Check if the wrapper itself is being monitored
    @monitor()
    async def outer_function():
        capture.log_event("outer_function: Starting")
        
        @monitor()  # Nested monitoring
        async def inner_async_gen():
            capture.log_event("inner_async_gen: Starting")
            yield 1
            raise ValueError("Nested error")
        
        values = []
        try:
            async for v in inner_async_gen():
                values.append(v)
        except ValueError:
            capture.log_event("outer_function: Caught error from inner")
        
        return values
    
    result = await outer_function()
    
    records = capture.capture_records()
    capture.analyze()
    
    print(f"\nFound {len(records)} records")
    # This might reveal if nesting is causing extra records


async def test_async_generator_cleanup_behavior():
    """Test 5: Understand async generator cleanup and finalization."""
    print("\n\n=== TEST 5: Async Generator Cleanup ===")
    capture = RecordCapture()
    queue = get_observability_queue()
    queue.clear()
    
    @monitor()
    async def generator_with_cleanup():
        capture.log_event("generator_with_cleanup: Starting")
        try:
            yield 1
            yield 2
            raise ValueError("Error in generator")
        finally:
            capture.log_event("generator_with_cleanup: Cleanup in finally")
            # Sometimes cleanup can trigger additional monitoring
    
    gen = generator_with_cleanup()
    values = []
    
    try:
        async for value in gen:
            values.append(value)
    except ValueError:
        capture.log_event("Main: Caught ValueError")
    
    # Force cleanup
    capture.log_event("Main: Calling aclose()")
    try:
        await gen.aclose()
    except:
        capture.log_event("Main: aclose() raised")
    
    records = capture.capture_records()
    capture.analyze()


async def run_all_tests():
    """Run all investigation tests."""
    await test_basic_async_generator()
    await test_async_generator_with_exception_in_iteration()
    await test_async_generator_wrapper_details()
    await test_multiple_monitor_decorators()
    await test_async_generator_cleanup_behavior()
    
    print("\n=== INVESTIGATION COMPLETE ===")
    print("Key findings will be documented in the robustness analysis.")


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 