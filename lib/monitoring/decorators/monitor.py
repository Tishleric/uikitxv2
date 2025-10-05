"""Monitor decorator for observatory system - Phase 8 with performance optimizations

LEGACY NOTICE:
- This decorator implements function-level tracing intended primarily for
  development diagnostics. It is not the service-health framework. For
  operational monitoring of pipeline services (completeness, correctness,
  timeliness), use the BigBrother system under `lib/big_brother/`.

SCOPE:
- Keep usage narrow and intentional. The repository discourages blanket
  application of this decorator in application code.

Environment Variables:
    MONITOR_LOG_LEVEL: Controls console output verbosity
        - "ERROR": Only show failed executions
        - "WARNING": Show failures and warnings (default)
        - "INFO": Show all executions
        - "QUIET": Suppress all output
    
    MONITOR_QUIET: Legacy option, if set to any value, suppresses all output
    
    MONITOR_PROFILING: If set to "1", enables cProfile profiling for decorated functions
"""

import functools
import os
import time
import traceback
import random
import asyncio
import inspect
import threading
import cProfile
import pstats
import io
from typing import Callable, Optional, Any, Dict, List, Tuple
from datetime import datetime
from collections import namedtuple

from lib.monitoring.serializers import SmartSerializer
from lib.monitoring.queues import ObservatoryQueue, ObservatoryRecord
from lib.monitoring.writers import BatchWriter
from lib.monitoring.performance import FastSerializer, MetadataCache, get_metadata_cache
from lib.monitoring.resource_monitor import get_resource_monitor, ResourceSnapshot
from lib.monitoring.retention import RetentionManager, RetentionController


# Global singleton queue instance
_observatory_queue = None
_batch_writer = None
_retention_controller = None


def get_observatory_queue() -> ObservatoryQueue:
    """Get or create the global observatory queue singleton."""
    global _observatory_queue
    if _observatory_queue is None:
        _observatory_queue = ObservatoryQueue()
    return _observatory_queue


def start_observatory_writer(db_path: str = "logs/observatory.db", 
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

    # Allow global disable via environment variable
    if os.environ.get("MONITOR_DISABLE") == "1":
        print("[MONITOR] MONITOR_DISABLE=1 set. Skipping observatory writer startup.")
        return None
    
    # Ensure queue exists
    queue = get_observatory_queue()
    
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
        print(f"[MONITOR] Started observatory writer → {db_path}")
    
    # Start retention controller if enabled
    if retention_enabled and _retention_controller is None:
        retention_manager = RetentionManager(db_path, retention_hours)
        _retention_controller = RetentionController(retention_manager)
        _retention_controller.start()
        print(f"[MONITOR] Started retention controller ({retention_hours} hour retention)")
    
    return _batch_writer


def stop_observatory_writer():
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
        print("[MONITOR] Stopped observatory writer")


def extract_parameter_names(func: Callable) -> Dict[str, Any]:
    """
    Extract parameter names and metadata from a function signature.
    
    Returns a dict with:
    - param_names: List of positional parameter names
    - param_defaults: Dict of parameter names to default values
    - varargs_name: Name of *args parameter (if any)
    - kwargs_name: Name of **kwargs parameter (if any)
    - has_self: Whether first parameter is 'self'
    - has_cls: Whether first parameter is 'cls'
    """
    metadata = {
        'param_names': [],
        'param_defaults': {},
        'varargs_name': None,
        'kwargs_name': None,
        'has_self': False,
        'has_cls': False,
    }
    
    try:
        # Get the signature
        sig = inspect.signature(func)
        
        # Process parameters in order
        for param_name, param in sig.parameters.items():
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                # This is *args
                metadata['varargs_name'] = param_name
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                # This is **kwargs
                metadata['kwargs_name'] = param_name
            elif param.kind in (inspect.Parameter.POSITIONAL_ONLY, 
                              inspect.Parameter.POSITIONAL_OR_KEYWORD):
                # Regular positional parameter
                metadata['param_names'].append(param_name)
                
                # Check if it has a default value
                if param.default != inspect.Parameter.empty:
                    metadata['param_defaults'][param_name] = param.default
                
                # Check for self/cls
                if len(metadata['param_names']) == 1:
                    if param_name == 'self':
                        metadata['has_self'] = True
                    elif param_name == 'cls':
                        metadata['has_cls'] = True
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                # Keyword-only parameter (after *)
                # Treat as regular parameter for our purposes
                metadata['param_names'].append(param_name)
                if param.default != inspect.Parameter.empty:
                    metadata['param_defaults'][param_name] = param.default
    
    except (ValueError, TypeError):
        # Some functions don't have inspectable signatures (e.g., C extensions)
        # Fall back to generic names
        pass
    
    return metadata


def map_args_to_names(args: tuple, kwargs: dict, param_metadata: Dict[str, Any], skip_self: bool = False) -> List[Tuple[str, Any, str]]:
    """
    Map function arguments to their parameter names.
    
    Args:
        args: Positional arguments
        kwargs: Keyword arguments
        param_metadata: Metadata from extract_parameter_names
        skip_self: Whether to skip 'self' parameter
    
    Returns:
        List of tuples: (param_name, value, data_type)
    """
    result = []
    param_names = param_metadata['param_names']
    varargs_name = param_metadata['varargs_name']
    
    # Skip self/cls if needed
    start_index = 0
    if skip_self and (param_metadata['has_self'] or param_metadata['has_cls']):
        start_index = 1
    
    # Map positional arguments
    for i, arg_value in enumerate(args):
        if i < len(param_names) - start_index:
            # Regular positional argument
            param_name = param_names[i + start_index]
            result.append((param_name, arg_value, "INPUT"))
        else:
            # Extra positional argument (part of *args)
            if varargs_name:
                param_name = f"{varargs_name}[{i - len(param_names) + start_index}]"
            else:
                param_name = f"arg_{i}"
            result.append((param_name, arg_value, "INPUT"))
    
    # Map keyword arguments
    for key, value in kwargs.items():
        result.append((key, value, "INPUT"))
    
    return result


def extract_return_names(func: Callable, result: Any) -> List[Tuple[str, Any, str]]:
    """
    Extract names for return values based on type hints, docstrings, or value types.
    
    Args:
        func: The function that returned the value
        result: The return value
    
    Returns:
        List of tuples: (name, value, data_type)
    """
    result_entries = []
    
    # Handle None explicitly - don't create entry
    if result is None:
        return []
    
    # Try to get return annotation
    try:
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation
        
        # Handle various return annotation types
        if return_annotation != inspect.Parameter.empty:
            # Check for typing.Tuple or tuple
            origin = getattr(return_annotation, '__origin__', None)
            args = getattr(return_annotation, '__args__', [])
                
            # If it's a Tuple annotation, try to extract individual names
            if origin is tuple and args:
                if isinstance(result, tuple) and len(result) == len(args):
                    # Try to get names from docstring
                    doc = func.__doc__ or ""
                    # Look for "Returns: (name1, name2, ...)" pattern
                    import re
                    returns_match = re.search(r'Returns?:\s*\(([^)]+)\)', doc)
                    if returns_match:
                        names = [n.strip() for n in returns_match.group(1).split(',')]
                        if len(names) == len(result):
                            for name, value in zip(names, result):
                                result_entries.append((name, value, "OUTPUT"))
                    return result_entries
    except:
        pass
    
    # Special handling for common return types
    if isinstance(result, tuple):
        # Handle navigation pattern (content, active_page, style1, style2, ...)
        if len(result) >= 3:
            # Check if this looks like a navigation return (content list, page string, style dicts)
            if (isinstance(result[0], list) and 
                isinstance(result[1], str) and
                all(isinstance(item, dict) and any(k in item for k in ('backgroundColor', 'color', 'border', 'padding')) 
                    for item in result[2:])):
                # It's a navigation pattern
                result_entries.append(("content", result[0], "OUTPUT"))
                result_entries.append(("active_page", result[1], "OUTPUT"))
                
                # Name the styles based on common navigation button names
                nav_names = ["pricing_monkey", "analysis", "greek_analysis", "logs", 
                            "project_docs", "scenario_ladder", "actant_eod", "actant_pnl", "observatory"]
                
                for i, (style, nav_name) in enumerate(zip(result[2:], nav_names)):
                    if i < len(nav_names):
                        result_entries.append((f"{nav_name}_style", style, "OUTPUT"))
                    else:
                        result_entries.append((f"nav_style_{i}", style, "OUTPUT"))
                
                return result_entries
        
        # Handle 2-item tuples with common patterns
        if len(result) == 2:
            # Check for (value, status) pattern
            if isinstance(result[1], bool):
                result_entries.append(("value", result[0], "OUTPUT"))
                result_entries.append(("status", result[1], "OUTPUT"))
                return result_entries
            # Check for (result, error) pattern
            elif result[1] is None or isinstance(result[1], Exception):
                result_entries.append(("result", result[0], "OUTPUT"))
                result_entries.append(("error", result[1], "OUTPUT"))
                return result_entries
        # Handle 3-item tuples (value, status, message)
        elif len(result) == 3:
            if isinstance(result[1], (int, bool)) and isinstance(result[2], str):
                result_entries.append(("value", result[0], "OUTPUT"))
                result_entries.append(("status", result[1], "OUTPUT"))
                result_entries.append(("message", result[2], "OUTPUT"))
                return result_entries
        
        # Special handling for Dash component returns
        if isinstance(result, (list, tuple)):
            component_names = []
            for i, item in enumerate(result):
                if hasattr(item, '__class__'):
                    class_name = item.__class__.__name__
                    # Check if it's a Dash component
                    if hasattr(item, 'id') and class_name in ['Div', 'Graph', 'DataTable', 'Container', 'Button', 'Input', 'Dropdown']:
                        comp_id = getattr(item, 'id', None)
                        if comp_id:
                            component_names.append((f"{class_name}[{comp_id}]", str(item)[:100], "OUTPUT"))
                        else:
                            component_names.append((f"{class_name}_{i}", str(item)[:100], "OUTPUT"))
                    else:
                        component_names.append((f"result_{i}", item, "OUTPUT"))
                else:
                    component_names.append((f"result_{i}", item, "OUTPUT"))
            return component_names
        
        # Default tuple handling
        for i, value in enumerate(result):
            result_entries.append((f"result_{i}", value, "OUTPUT"))
        return result_entries
    
    # Handle named tuples (check if it has _fields attribute)
    elif hasattr(result, '_fields'):
        for field in result._fields:
            value = getattr(result, field)
            result_entries.append((field, value, "OUTPUT"))
        return result_entries
    
    # Handle dataclasses
    elif hasattr(result, '__dataclass_fields__'):
        for field in result.__dataclass_fields__:
            value = getattr(result, field)
            result_entries.append((field, value, "OUTPUT"))
        return result_entries
    
    # Handle dictionaries
    elif isinstance(result, dict):
        for key, value in result.items():
            result_entries.append((f"result[{key}]", value, "OUTPUT"))
        return result_entries
    
    # Handle custom objects with meaningful attributes
    elif hasattr(result, '__dict__') and not isinstance(result, type):
        # Use the class name as a prefix
        class_name = result.__class__.__name__
        result_entries.append((class_name, result, "OUTPUT"))
        return result_entries
    
    # Special handling for Dash components with ID
    if isinstance(result, dict):
        # Check if it's a Dash component (has 'props' with 'id')
        if 'props' in result and isinstance(result['props'], dict):
            if 'id' in result['props']:
                component_type = result.get('type', 'Component')
                component_id = result['props']['id']
                return [(f"{component_type}[{component_id}]", result, "OUTPUT")]
            elif 'children' in result['props'] and isinstance(result['props']['children'], str):
                # Component with text content
                component_type = result.get('type', 'Component')
                text_preview = result['props']['children'][:30]
                return [(f"{component_type}[{text_preview}...]", result, "OUTPUT")]
        
        # Check if it's a style dictionary (common in Dash)
        style_keys = {'width', 'height', 'color', 'backgroundColor', 'display', 
                      'margin', 'padding', 'border', 'fontSize', 'textAlign'}
        if any(key in result for key in style_keys):
            # It's likely a style dictionary
            if 'cursor' in result and result.get('cursor') == 'pointer':
                return [("button_style", result, "OUTPUT")]
            elif 'display' in result and result.get('display') == 'flex':
                return [("flex_style", result, "OUTPUT")]
            else:
                return [("style", result, "OUTPUT")]
    
    # Default: single return value
    result_entries.append(("result", result, "OUTPUT"))
    return result_entries


# Cache for function parameter metadata
_param_metadata_cache = {}


def monitor(
    process_group: str = None,
    sample_rate: float = 1.0,
    capture: dict = None,
    serializer: str = "smart",
    max_repr: int = 1000,
    sensitive_fields: tuple = (),
    queue_warning_threshold: int = 8000,
    use_param_names: bool = True,  # New parameter to enable/disable parameter name extraction
    profiling_enabled: bool = False, # New parameter to enable/disable profiling
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
        use_param_names: Whether to extract actual parameter names (default: True)
        profiling_enabled: Whether to enable cProfile profiling for the decorated function
        
    Returns:
        Decorated function
    """
    # Global kill-switch: turn decorator into no-op if disabled
    if os.environ.get("MONITOR_DISABLE") == "1":
        def _noop_decorator(func_or_descriptor: Any) -> Any:
            return func_or_descriptor
        return _noop_decorator

    # Default: capture EVERYTHING (Track Everything philosophy)
    if capture is None:
        capture = {
            "args": True,
            "result": True,
            "cpu_usage": True,
            "memory_usage": True,
            "locals": True,  # Changed to True - capture everything by default
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
        
        # Build the full process name for this function
        process_name = f"{final_process_group}.{func_name}"
        
        # Extract parameter metadata once and cache it
        func_id = id(func)
        if use_param_names and func_id not in _param_metadata_cache:
            _param_metadata_cache[func_id] = extract_parameter_names(func)
        
        # Determine function type
        is_async = asyncio.iscoroutinefunction(func)
        is_async_generator = inspect.isasyncgenfunction(func)
        is_generator = inspect.isgeneratorfunction(func) and not is_async_generator
        
        # Check if this is a method (has self or cls)
        param_metadata = _param_metadata_cache.get(func_id, {})
        is_method = param_metadata.get('has_self', False) or param_metadata.get('has_cls', False)
        
        def create_record(start_time: float, status: str, exception_str: Optional[str], 
                         args: tuple, kwargs: dict, result: Any = None, 
                         start_snapshot: Optional[ResourceSnapshot] = None) -> ObservatoryRecord:
            """Helper to create observatory record"""
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Calculate CPU and memory deltas if enabled
            cpu_delta = None
            memory_delta_mb = None
            
            if (capture.get("cpu_usage") or capture.get("memory_usage")) and start_snapshot is not None:
                resource_monitor = get_resource_monitor()
                cpu_delta, memory_delta_mb = resource_monitor.measure_resources(start_snapshot)
            
            # Get queue and serializer
            queue = get_observatory_queue()
            
            # Use FastSerializer for performance, fallback to SmartSerializer for sensitive data
            if sensitive_fields:
                serializer_obj = SmartSerializer(max_repr=max_repr, sensitive_fields=sensitive_fields)
            else:
                serializer_obj = FastSerializer()
            
            # Build process name
            process = f"{final_process_group}.{func_name}"
            
            # Map arguments to parameter names if enabled
            if use_param_names and func_id in _param_metadata_cache:
                param_metadata = _param_metadata_cache[func_id]
                param_mappings = map_args_to_names(args, kwargs, param_metadata, skip_self=is_method)
            else:
                # Fallback to generic names
                param_mappings = []
                for i, arg_value in enumerate(args):
                    param_mappings.append((f"arg_{i}", arg_value, "INPUT"))
                for key, value in kwargs.items():
                    param_mappings.append((key, value, "INPUT"))
            
            # Extract return value names if result is present
            result_mappings = []
            if capture.get("result") and result is not None:
                if use_param_names:
                    result_mappings = extract_return_names(func, result)
                else:
                    result_mappings = [("result", result, "OUTPUT")]
            
            # Serialize all values
            serialized_mappings = []
            
            # Serialize input parameters
            if capture.get("args"):
                for param_name, value, data_type in param_mappings:
                    try:
                        if isinstance(serializer_obj, FastSerializer):
                            serialized_value = serializer_obj.lazy_serialize(value)
                        else:
                            serialized_value = serializer_obj.serialize(value, param_name)
                        serialized_mappings.append((param_name, serialized_value, data_type))
                    except:
                        serialized_mappings.append((param_name, "<serialization failed>", data_type))
            
            # Serialize output parameters
            for param_name, value, data_type in result_mappings:
                try:
                    if isinstance(serializer_obj, FastSerializer):
                        serialized_value = serializer_obj.lazy_serialize(value)
                    else:
                        serialized_value = serializer_obj.serialize(value, param_name)
                    serialized_mappings.append((param_name, serialized_value, data_type))
                except:
                    serialized_mappings.append((param_name, "<serialization failed>", data_type))
            
            # Create record with parent-child tracking fields
            start_ts_us = int(start_time * 1_000_000)  # Convert to microseconds
            thread_id = threading.get_ident()
            # Get call depth, adjusting for decorator layers
            # Subtract some frames for: create_record, wrapper, decorator, etc.
            call_depth = max(0, len(inspect.stack()) - 5)
            
            # Store the parameter mappings in a custom field for the writer
            record = ObservatoryRecord(
                ts=datetime.now().isoformat(),
                process=process,
                status=status,
                duration_ms=duration_ms,
                exception=exception_str,
                args=None,  # We'll use parameter_mappings instead
                kwargs=None,  # We'll use parameter_mappings instead
                result=None,  # We'll use parameter_mappings instead
                thread_id=thread_id,
                call_depth=call_depth,
                start_ts_us=start_ts_us,
                cpu_delta=cpu_delta,
                memory_delta_mb=memory_delta_mb
            )
            
            # Add custom field for parameter mappings
            record.parameter_mappings = serialized_mappings
            
            # Send to queue
            queue.put(record)
            
            # Console output with log level control
            # Support both MONITOR_QUIET (legacy) and MONITOR_LOG_LEVEL (new)
            quiet_mode = os.environ.get("MONITOR_QUIET")
            log_level = os.environ.get("MONITOR_LOG_LEVEL", "WARNING").upper()
            
            # If MONITOR_QUIET is set, honor it for backward compatibility
            if quiet_mode:
                log_level = "QUIET"
            
            # Determine what to show based on log level
            show_errors = log_level in ["ERROR", "WARNING", "INFO"]
            show_warnings = log_level in ["WARNING", "INFO"]
            show_info = log_level == "INFO"
            
            # Log based on status and level
            if status == "OK" and show_info:
                print(f"[MONITOR] {process} executed in {duration_ms:.3f}ms")
            elif status != "OK" and show_errors:
                print(f"[MONITOR] {process} failed after {duration_ms:.3f}ms")
            
            # Check queue size and show warning if appropriate
            if show_warnings:
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
                
                # Check if profiling is enabled globally or for this function
                enable_profiling = profiling_enabled or os.environ.get("MONITOR_PROFILING") == "1"
                
                start_time = time.perf_counter()
                start_snapshot = None
                profiler = None
                
                # Simple profiling with cProfile
                if enable_profiling:
                    try:
                        profiler = cProfile.Profile()
                        profiler.enable()
                    except ValueError:
                        # Another profiler is already active
                        profiler = None
                
                # Take resource snapshot at start if enabled
                if capture.get("cpu_usage") or capture.get("memory_usage"):
                    resource_monitor = get_resource_monitor()
                    if resource_monitor.is_available():
                        start_snapshot = resource_monitor.take_snapshot()
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Stop profiling if enabled
                    profile_stats = None
                    if profiler:
                        profiler.disable()
                        s = io.StringIO()
                        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                        ps.print_stats(20)  # Top 20 functions
                        profile_stats = s.getvalue()
                    
                    # Record success
                    record = create_record(start_time, "OK", None, args, kwargs, result, start_snapshot)
                    
                    # Add profile stats to the record if available
                    if profile_stats and record:
                        # Store profile stats in the exception field with a marker
                        record.exception = f"[PROFILE]\n{profile_stats}"
                    
                    return result
                    
                except Exception as e:
                    # Stop profiling if enabled
                    if profiler:
                        profiler.disable()
                    
                    # Record error
                    tb = traceback.format_exc()
                    record = create_record(start_time, "ERR", tb, args, kwargs, None, start_snapshot)
                    
                    raise
            
            return sync_wrapper
    
    return decorator

# Compatibility aliases for old function names
start_observability_writer = start_observatory_writer
stop_observability_writer = stop_observatory_writer
get_observability_queue = get_observatory_queue 