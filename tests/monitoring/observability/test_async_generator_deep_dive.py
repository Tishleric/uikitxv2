"""Deep dive into async generator double-recording issue."""

import asyncio
import inspect
from lib.monitoring.decorators.monitor import monitor, get_observability_queue


async def test_wrapper_inspection():
    """Inspect what happens when we wrap an async generator."""
    print("\n=== WRAPPER INSPECTION ===")
    
    queue = get_observability_queue()
    queue.clear()
    
    @monitor()
    async def my_async_gen():
        print(f"my_async_gen type: {type(my_async_gen)}")
        print(f"Is async gen function: {inspect.isasyncgenfunction(my_async_gen)}")
        yield 1
        raise ValueError("Test error")
    
    print(f"\nWrapped function type: {type(my_async_gen)}")
    print(f"Is wrapped still async gen: {inspect.isasyncgenfunction(my_async_gen)}")
    
    # Create generator
    print("\nCreating generator...")
    gen = my_async_gen()
    print(f"Generator type: {type(gen)}")
    print(f"Generator object: {gen}")
    
    # Check if our wrapper returns a wrapper generator
    print(f"\nChecking wrapper details...")
    print(f"__name__: {my_async_gen.__name__}")
    print(f"__wrapped__: {getattr(my_async_gen, '__wrapped__', 'None')}")
    
    # Iterate and catch exception
    values = []
    try:
        async for val in gen:
            print(f"Got value: {val}")
            values.append(val)
    except ValueError as e:
        print(f"Caught exception: {e}")
    
    # Check records
    records = queue.drain(10)
    print(f"\nTotal records: {len(records)}")
    for i, rec in enumerate(records):
        print(f"Record {i}: {rec.status} - {rec.duration_ms:.3f}ms")


async def test_manual_wrapper():
    """Test with a manual async generator wrapper to understand behavior."""
    print("\n\n=== MANUAL WRAPPER TEST ===")
    
    queue = get_observability_queue()
    queue.clear()
    
    async def original_gen():
        """Original generator without decoration."""
        print("Original: yielding 1")
        yield 1
        print("Original: about to raise")
        raise ValueError("Manual test error")
    
    async def manual_wrapper():
        """Manual wrapper that mimics our monitor behavior."""
        print("Wrapper: Creating generator")
        gen = original_gen()
        print("Wrapper: Recording creation")
        # Simulate create_record for OK
        
        print("Wrapper: Starting iteration")
        async for item in gen:
            print(f"Wrapper: yielding {item}")
            yield item
        print("Wrapper: Iteration complete (shouldn't reach here)")
    
    # Now wrap with monitor
    wrapped = monitor()(manual_wrapper)
    
    # Iterate
    gen = wrapped()
    values = []
    try:
        async for val in gen:
            print(f"Main: got {val}")
            values.append(val)
    except ValueError as e:
        print(f"Main: caught {e}")
    
    records = queue.drain(10)
    print(f"\nRecords from manual wrapper: {len(records)}")


async def test_simplified_case():
    """Simplified test case to isolate the issue."""
    print("\n\n=== SIMPLIFIED CASE ===")
    
    queue = get_observability_queue()
    queue.clear()
    
    call_count = 0
    
    @monitor()
    async def simple_error_gen():
        nonlocal call_count
        call_count += 1
        print(f"Generator called (count: {call_count})")
        yield 1
        raise ValueError("Simple error")
    
    # Create and iterate
    gen = simple_error_gen()
    try:
        async for _ in gen:
            pass
    except ValueError:
        pass
    
    print(f"\nFunction was called {call_count} times")
    
    records = queue.drain(10)
    print(f"Total records: {len(records)}")
    
    # Detailed record analysis
    for i, rec in enumerate(records):
        print(f"\nRecord {i}:")
        print(f"  Status: {rec.status}")
        print(f"  Duration: {rec.duration_ms:.3f}ms")
        print(f"  Process: {rec.process}")
        if rec.exception:
            # Get just the exception type and message
            lines = rec.exception.strip().split('\n')
            print(f"  Exception: {lines[-1] if lines else 'Unknown'}")


async def run_all():
    """Run all tests."""
    await test_wrapper_inspection()
    await test_manual_wrapper()
    await test_simplified_case()


if __name__ == "__main__":
    asyncio.run(run_all()) 