"""Monitor decorator for observability system - Phase 8 with performance optimizations"""

import functools
import os
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
from lib.monitoring.resource_monitor import get_resource_monitor, ResourceSnapshot
from lib.monitoring.retention import RetentionManager, RetentionController


# Global singleton queue instance
_observability_queue = None
_batch_writer = None
_retention_controller = None


def get_observability_queue() -> ObservabilityQueue:
    """Get or create the global observability queue singleton."""
    global _observability_queue
    if _observability_queue is None:
        _observability_queue = ObservabilityQueue()
    return _observability_queue


def start_observability_writer(db_path: str = "logs/observability.db", 
                              batch_size: int = 100, 
                              drain_interval: float = 0.1,
                              retention_hours: int = 6,
                              retention_enabled: bool = True):
    """Start the global batch writer and optionally the retention controller.
    
    Args:
        db_path: Path to SQLite database
        batch_size: Number of records to write in each batch
        drain_interval: Seconds between drain cycles
        retention_hours: Hours of data to retain (default: 6)
        retention_enabled: Whether to enable automatic retention (default: True)
    """
    global _batch_writer, _retention_controller
    
    # Ensure queue exists
    queue = get_observability_queue()
    
    # Start batch writer
    if _batch_writer is None:
        # Create writer with updated parameter order
        _batch_writer = BatchWriter(
            db_path=db_path,
            queue=queue,
            batch_size=batch_size,
            drain_interval=drain_interval
        )
        if retention_enabled:
            # Also start retention management
            global _retention_controller
            retention_manager = RetentionManager(db_path, retention_hours)
            _retention_controller = RetentionController(retention_manager)
        _batch_writer.start()
        print(f"[MONITOR] Started observability writer → {db_path}")
    
    # Start retention controller if enabled
    if retention_enabled and _retention_controller is None:
        retention_manager = RetentionManager(db_path, retention_hours)
        _retention_controller = RetentionController(retention_manager)
        _retention_controller.start()
        print(f"[MONITOR] Started retention controller ({retention_hours} hour retention)")
    
    return _batch_writer


def stop_observability_writer():
    """Stop the global batch writer and retention controller."""
    global _batch_writer, _retention_controller
    
    # Stop retention controller first
    if _retention_controller is not None:
        _retention_controller.stop()
        _retention_controller = None
        print("[MONITOR] Stopped retention controller")
    
    # Then stop batch writer
    if _batch_writer is not None:
        _batch_writer.stop()
        _batch_writer = None
        print("[MONITOR] Stopped observability writer")


def monitor(
    process_group: str = None,
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
                      If None, automatically derived from module name
        sample_rate: Sampling rate from 0.0 to 1.0 (1.0 = always monitor)
        capture: Dict specifying what to capture (default: EVERYTHING)
                 Set to False or {} to disable specific captures
        serializer: Serialization strategy (default: "smart")
        max_repr: Maximum length for serialized values
        sensitive_fields: Field names to mask in serialization
        queue_warning_threshold: Queue size to trigger warnings
        
    Returns:
        Decorated function
    """
    # Default: capture EVERYTHING (Track Everything philosophy)
    if capture is None:
        capture = {
            "args": True,
            "result": True,
            "cpu_usage": True,
            "memory_usage": True,
            "locals": False,  # Still opt-in for locals due to verbosity
        }
    
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
        
        # Auto-derive process_group if not provided
        if process_group is None:
            # Use module name as process group (e.g., "lib.trading.actant")
            final_process_group = func_module
        else:
            final_process_group = process_group
        
        # Determine function type
        is_async = asyncio.iscoroutinefunction(func)
        is_async_generator = inspect.isasyncgenfunction(func)
        is_generator = inspect.isgeneratorfunction(func) and not is_async_generator
        
        def create_record(start_time: float, status: str, exception_str: Optional[str], 
                         args: tuple, kwargs: dict, result: Any = None, 
                         start_snapshot: Optional[ResourceSnapshot] = None) -> ObservabilityRecord:
            """Helper to create observability record"""
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Calculate CPU and memory deltas if enabled
            cpu_delta = None
            memory_delta_mb = None
            
            if (capture.get("cpu_usage") or capture.get("memory_usage")) and start_snapshot is not None:
                resource_monitor = get_resource_monitor()
                cpu_delta, memory_delta_mb = resource_monitor.measure_resources(start_snapshot)
            
            # Get queue and serializer
            queue = get_observability_queue()
            
            # Use FastSerializer for performance, fallback to SmartSerializer for sensitive data
            if sensitive_fields:
                serializer_obj = SmartSerializer(max_repr=max_repr, sensitive_fields=sensitive_fields)
            else:
                serializer_obj = FastSerializer()
            
            # Build process name
            process = f"{final_process_group}.{func_name}"
            
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
                start_ts_us=start_ts_us,
                cpu_delta=cpu_delta,
                memory_delta_mb=memory_delta_mb
            )
            
            # Send to queue
            queue.put(record)
            
            # Console output (skip if in benchmark mode)
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
                start_snapshot = None
                iteration_started = False
                
                # Take resource snapshot at start if enabled
                if capture.get("cpu_usage") or capture.get("memory_usage"):
                    resource_monitor = get_resource_monitor()
                    if resource_monitor.is_available():
                        start_snapshot = resource_monitor.take_snapshot()
                
                try:
                    # Create the async generator
                    gen = func(*args, **kwargs)
                    
                    # Record successful creation
                    create_record(start_time, "OK", None, args, kwargs, gen, start_snapshot)
                    
                    # Yield all values from the generator
                    async for item in gen:
                        iteration_started = True
                        yield item
                        
                except Exception as e:
                    # Record error with proper timing
                    tb = traceback.format_exc()
                    # If we were iterating, this is an iteration error
                    # If not, this is a creation error
                    # Either way, record it once with the original start time
                    if not iteration_started:
                        # Exception during generator creation (before first yield)
                        create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
                    else:
                        # Exception during iteration - record with full duration
                        create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
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
                start_snapshot = None
                
                # Take resource snapshot at start if enabled
                if capture.get("cpu_usage") or capture.get("memory_usage"):
                    resource_monitor = get_resource_monitor()
                    if resource_monitor.is_available():
                        start_snapshot = resource_monitor.take_snapshot()
                
                try:
                    # Execute the async function
                    result = await func(*args, **kwargs)
                    
                    # Record success
                    create_record(start_time, "OK", None, args, kwargs, result, start_snapshot)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
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
                start_snapshot = None
                
                # Take resource snapshot at start if enabled
                if capture.get("cpu_usage") or capture.get("memory_usage"):
                    resource_monitor = get_resource_monitor()
                    if resource_monitor.is_available():
                        start_snapshot = resource_monitor.take_snapshot()
                
                try:
                    # Create the generator
                    gen = func(*args, **kwargs)
                    
                    # Record successful creation
                    create_record(start_time, "OK", None, args, kwargs, gen, start_snapshot)
                    
                    # Yield all values from the generator
                    yield from gen
                    
                except Exception as e:
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
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
                start_snapshot = None
                
                # Take resource snapshot at start if enabled
                if capture.get("cpu_usage") or capture.get("memory_usage"):
                    resource_monitor = get_resource_monitor()
                    if resource_monitor.is_available():
                        start_snapshot = resource_monitor.take_snapshot()
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Record success
                    create_record(start_time, "OK", None, args, kwargs, result, start_snapshot)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    tb = traceback.format_exc()
                    create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
                    raise
            
            return sync_wrapper
    
    return decorator 