"""Monitor decorator for observability system - Phase 8 with performance optimizations"""

import functools
import time
import traceback
import random
import asyncio
import inspect
import threading
from typing import Callable, Optional, Any
from datetime import datetime

from lib.monitoring.serializers import SmartSerializer
from lib.monitoring.queues import ObservabilityQueue, ObservabilityRecord
from lib.monitoring.writers import BatchWriter
from lib.monitoring.performance import FastSerializer, MetadataCache, get_metadata_cache


# Global singleton queue instance
_observability_queue = None
_batch_writer = None


def get_observability_queue() -> ObservabilityQueue:
    """Get or create the global observability queue singleton."""
    global _observability_queue
    if _observability_queue is None:
        _observability_queue = ObservabilityQueue()
    return _observability_queue


def start_observability_writer(db_path: str = "logs/observability.db", batch_size: int = 100, drain_interval: float = 0.1):
    """Start the global batch writer if not already running."""
    global _batch_writer
    if _batch_writer is None:
        queue = get_observability_queue()
        _batch_writer = BatchWriter(queue, db_path, batch_size, drain_interval)
        _batch_writer.start()
        print(f"[MONITOR] Started observability writer → {db_path}")
    return _batch_writer


def stop_observability_writer():
    """Stop the global batch writer."""
    global _batch_writer
    if _batch_writer is not None:
        _batch_writer.stop()
        _batch_writer = None
        print("[MONITOR] Stopped observability writer")


def monitor(
    process_group: str,
    sample_rate: float = 1.0,
    capture: dict = None,
    serializer: str = "smart",
    max_repr: int = 1000,
    sensitive_fields: tuple = (),
    queue_warning_threshold: int = 8000,
) -> Callable:
    """
    Decorator to monitor function execution and capture data.
    
    Supports:
    - Regular sync functions
    - Async functions (async def)
    - Generators (functions with yield)
    - Async generators (async def with yield)
    - Class methods, static methods, and instance methods
    
    Args:
        process_group: Logical grouping for the function (e.g., "trading.actant")
        sample_rate: Sampling rate from 0.0 to 1.0 (1.0 = always monitor)
        capture: Dict specifying what to capture (default: args and result)
        serializer: Serialization strategy (default: "smart")
        max_repr: Maximum length for serialized values
        sensitive_fields: Field names to mask in serialization
        queue_warning_threshold: Queue size to trigger warnings
        
    Returns:
        Decorated function
    """
    if capture is None:
        capture = {"args": True, "result": True, "locals": False}
    
    def decorator(func_or_descriptor: Any) -> Any:
        # Handle descriptors (classmethod, staticmethod)
        is_classmethod = isinstance(func_or_descriptor, classmethod)
        is_staticmethod = isinstance(func_or_descriptor, staticmethod)
        
        if is_classmethod or is_staticmethod:
            # Extract the actual function from the descriptor
            actual_func = func_or_descriptor.__func__
            # Decorate the actual function
            wrapped_func = decorator(actual_func)
            # Return the descriptor with the wrapped function
            if is_classmethod:
                return classmethod(wrapped_func)
            else:
                return staticmethod(wrapped_func)
        
        # Normal function decoration
        func = func_or_descriptor
        
        # Get function metadata (cached)
        metadata_cache = get_metadata_cache()
        func_metadata = metadata_cache.cache_function_metadata(func)
        func_module = func_metadata["module"]
        func_name = func_metadata["name"]
        func_qualname = func_metadata["qualname"]
        
        # Determine function type
        is_async = asyncio.iscoroutinefunction(func)
        is_async_generator = inspect.isasyncgenfunction(func)
        is_generator = inspect.isgeneratorfunction(func) and not is_async_generator
        
        def create_record(start_time: float, status: str, exception_str: Optional[str], 
                         args: tuple, kwargs: dict, result: Any = None) -> ObservabilityRecord:
            """Helper to create observability record"""
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Get queue and serializer
            queue = get_observability_queue()
            
            # Use FastSerializer for performance, fallback to SmartSerializer for sensitive data
            if sensitive_fields:
                serializer_obj = SmartSerializer(max_repr=max_repr, sensitive_fields=sensitive_fields)
            else:
                serializer_obj = FastSerializer()
            
            # Build process name
            process = f"{process_group}.{func_module}.{func_name}"
            
            # Serialize captured data
            serialized_args = None
            serialized_kwargs = None
            serialized_result = None
            
            if capture.get("args"):
                try:
                    # Use lazy serialization for large arguments
                    if isinstance(serializer_obj, FastSerializer):
                        serialized_args = [serializer_obj.lazy_serialize(arg) for arg in args] if args else None
                        serialized_kwargs = {k: serializer_obj.lazy_serialize(v) for k, v in kwargs.items()} if kwargs else None
                    else:
                        serialized_args = [serializer_obj.serialize(arg) for arg in args] if args else None
                        serialized_kwargs = {k: serializer_obj.serialize(v, k) for k, v in kwargs.items()} if kwargs else None
                except:
                    serialized_args = ["<serialization failed>"]
            
            if capture.get("result") and result is not None:
                if isinstance(serializer_obj, FastSerializer):
                    serialized_result = serializer_obj.lazy_serialize(result)
                else:
                    serialized_result = serializer_obj.serialize(result)
            
            # Create record with parent-child tracking fields
            start_ts_us = int(start_time * 1_000_000)  # Convert to microseconds
            thread_id = threading.get_ident()
            # Get call depth, adjusting for decorator layers
            # Subtract some frames for: create_record, wrapper, decorator, etc.
            call_depth = max(0, len(inspect.stack()) - 5)
            
            record = ObservabilityRecord(
                ts=datetime.now().isoformat(),
                process=process,
                status=status,
                duration_ms=duration_ms,
                exception=exception_str,
                args=serialized_args,
                kwargs=serialized_kwargs,
                result=serialized_result,
                thread_id=thread_id,
                call_depth=call_depth,
                start_ts_us=start_ts_us
            )
            
            # Send to queue
            queue.put(record)
            
            # Console output (skip if in benchmark mode)
            import os
            if not os.environ.get("MONITOR_QUIET"):
                if status == "OK":
                    print(f"[MONITOR] {process} executed in {duration_ms:.3f}ms")
                else:
                    print(f"[MONITOR] {process} failed after {duration_ms:.3f}ms")
                
                # Check queue size
                stats = queue.get_queue_stats()
                if stats['normal_queue_size'] > queue_warning_threshold:
                    print(f"[MONITOR] WARNING: Queue size {stats['normal_queue_size']} exceeds threshold {queue_warning_threshold}")
            
            return record
        
        # Create appropriate wrapper based on function type
        if is_async_generator:
            # Async generator wrapper
            @functools.wraps(func)
            async def async_gen_wrapper(*args, **kwargs):
                # Check sampling rate
                if sample_rate < 1.0 and random.random() > sample_rate:
                    async for item in func(*args, **kwargs):
                        yield item
                    return
                
                start_time = time.perf_counter()
                
                try:
                    # Create the async generator
                    gen = func(*args, **kwargs)
                    
                    # Record successful creation
                    create_record(start_time, "OK", None, args, kwargs, gen)
                    
                    # Yield all values from the generator
                    async for item in gen:
                        yield item
                        
                except Exception as e:
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs)
                    raise
            
            return async_gen_wrapper
            
        elif is_async:
            # Async function wrapper
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Check sampling rate
                if sample_rate < 1.0 and random.random() > sample_rate:
                    return await func(*args, **kwargs)
                
                start_time = time.perf_counter()
                
                try:
                    # Execute the async function
                    result = await func(*args, **kwargs)
                    
                    # Record success
                    create_record(start_time, "OK", None, args, kwargs, result)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs)
                    raise
            
            return async_wrapper
            
        elif is_generator:
            # Generator wrapper
            @functools.wraps(func)
            def gen_wrapper(*args, **kwargs):
                # Check sampling rate
                if sample_rate < 1.0 and random.random() > sample_rate:
                    yield from func(*args, **kwargs)
                    return
                
                start_time = time.perf_counter()
                
                try:
                    # Create the generator
                    gen = func(*args, **kwargs)
                    
                    # Record successful creation
                    create_record(start_time, "OK", None, args, kwargs, gen)
                    
                    # Yield all values from the generator
                    yield from gen
                    
                except Exception as e:
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs)
                    raise
            
            return gen_wrapper
            
        else:
            # Regular sync function wrapper (existing implementation)
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Check sampling rate
                if sample_rate < 1.0 and random.random() > sample_rate:
                    return func(*args, **kwargs)
                
                start_time = time.perf_counter()
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Record success
                    create_record(start_time, "OK", None, args, kwargs, result)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs)
                    raise
            
            return sync_wrapper
    
    return decorator 