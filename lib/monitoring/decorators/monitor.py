"""Monitor decorator for observability system - Phase 6 complete integration"""

import functools
import time
import traceback
import random
from typing import Callable, Optional
from datetime import datetime

from lib.monitoring.serializers import SmartSerializer
from lib.monitoring.queues import ObservabilityQueue, ObservabilityRecord
from lib.monitoring.writers import BatchWriter


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
    
    Complete integration with ObservabilityQueue and SmartSerializer.
    
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
    
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        func_module = func.__module__
        func_name = func.__name__
        func_qualname = func.__qualname__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check sampling rate
            if sample_rate < 1.0 and random.random() > sample_rate:
                # Skip monitoring for this call
                return func(*args, **kwargs)
            
            # Get queue and serializer
            queue = get_observability_queue()
            serializer_obj = SmartSerializer(max_repr=max_repr, sensitive_fields=sensitive_fields)
            
            # Build process name
            process = f"{process_group}.{func_module}.{func_name}"
            
            # Start timing
            start_time = time.perf_counter()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Serialize captured data
                serialized_args = None
                serialized_kwargs = None
                serialized_result = None
                
                if capture.get("args"):
                    serialized_args = [serializer_obj.serialize(arg) for arg in args] if args else None
                    serialized_kwargs = {k: serializer_obj.serialize(v, k) for k, v in kwargs.items()} if kwargs else None
                
                if capture.get("result"):
                    serialized_result = serializer_obj.serialize(result)
                
                # Create observability record
                record = ObservabilityRecord(
                    ts=datetime.now().isoformat(),
                    process=process,
                    status="OK",
                    duration_ms=duration_ms,
                    exception=None,
                    args=serialized_args,
                    kwargs=serialized_kwargs,
                    result=serialized_result
                )
                
                # Send to queue
                queue.put(record)
                
                # Console output (keep for immediate feedback)
                print(f"[MONITOR] {process} executed in {duration_ms:.3f}ms")
                
                # Check queue size and warn if needed
                stats = queue.get_queue_stats()
                if stats['normal_queue_size'] > queue_warning_threshold:
                    print(f"[MONITOR] WARNING: Queue size {stats['normal_queue_size']} exceeds threshold {queue_warning_threshold}")
                
                return result
                
            except Exception as e:
                # Calculate duration even on exception
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Capture full traceback
                tb = traceback.format_exc()
                
                # Serialize captured data (args might have been the cause)
                serialized_args = None
                serialized_kwargs = None
                
                if capture.get("args"):
                    try:
                        serialized_args = [serializer_obj.serialize(arg) for arg in args] if args else None
                        serialized_kwargs = {k: serializer_obj.serialize(v, k) for k, v in kwargs.items()} if kwargs else None
                    except:
                        # If serialization fails, note it
                        serialized_args = ["<serialization failed>"]
                
                # Create error record
                record = ObservabilityRecord(
                    ts=datetime.now().isoformat(),
                    process=process,
                    status="ERR",
                    duration_ms=duration_ms,
                    exception=tb,
                    args=serialized_args,
                    kwargs=serialized_kwargs,
                    result=None
                )
                
                # Send to queue (errors have priority)
                queue.put(record)
                
                # Console output for errors
                print(f"[MONITOR] {process} failed after {duration_ms:.3f}ms: {type(e).__name__}: {e}")
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator 