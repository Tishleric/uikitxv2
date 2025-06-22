# Edge Cases and Limitations

## Overview

The observability system handles 99% of Python patterns perfectly. This document covers the 1% that requires special attention or alternative approaches.

## Known Limitations

### 1. Multiprocessing and Forked Processes

**Issue**: The @monitor decorator uses thread-local storage and a singleton queue that doesn't cross process boundaries.

**Symptoms**:
- No traces from child processes
- Queue statistics don't include forked work

**Workaround**:
```python
# Option 1: Use threading instead of multiprocessing
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=10)

# Option 2: Initialize observability in each process
def worker_init():
    from monitoring.writers import start_observability_writer
    start_observability_writer()

with ProcessPoolExecutor(initializer=worker_init) as executor:
    executor.map(monitored_function, data)
```

### 2. C Extensions and Native Code

**Issue**: Cannot monitor execution inside C extensions (NumPy operations, database drivers, etc.)

**Example**:
```python
@monitor()
def process_data(arr):
    # This Python code is monitored
    result = arr.copy()
    
    # This C code inside NumPy is not monitored
    return np.fft.fft(result)  # Actual FFT time not captured
```

**Workaround**: Monitor at the Python boundary
```python
@monitor(process_group="numpy.fft")
def fft_wrapper(arr):
    return np.fft.fft(arr)
```

### 3. Extremely Long String Representations

**Issue**: Some objects generate massive string representations that can consume excessive memory.

**Problem Example**:
```python
class BadClass:
    def __repr__(self):
        return "x" * 10_000_000  # 10MB string!
```

**Solution**: SmartSerializer truncates at 10,000 characters
```python
# Automatically handled:
# "<BadClass instance... truncated >"
```

### 4. Infinite Generators

**Issue**: Generators that never terminate can't be fully monitored.

**Example**:
```python
@monitor()
def infinite_stream():
    while True:
        yield random.random()
```

**Limitation**: Only generator creation is monitored, not individual yields

**Workaround**: Monitor the consumption point
```python
@monitor()
def process_batch(stream, count=100):
    return list(itertools.islice(stream, count))
```

### 5. Dynamic Function Creation

**Issue**: Functions created dynamically may have poor metadata.

**Example**:
```python
# These have limited metadata
func = lambda x: x * 2
exec("def dynamic(): return 42")
```

**Result**: Generic names like "<lambda>" in traces

**Workaround**: Use proper function definitions
```python
def multiplier(x):
    return x * 2
```

### 6. Coroutine Cleanup

**Issue**: Unawaited coroutines generate warnings and aren't monitored properly.

**Problem**:
```python
@monitor()
async def fetch_data():
    return await api_call()

# Wrong - coroutine never runs
coro = fetch_data()  # Warning: unawaited coroutine
```

**Solution**: Always await async functions
```python
# Correct
result = await fetch_data()
```

### 7. Thread-Local State in Async

**Issue**: Thread-local storage doesn't work well with async context switches.

**Impact**: Parent-child relationships may be incorrect in complex async scenarios

**Workaround**: Use contextvars (planned for Phase 9+)
```python
# Future enhancement
from contextvars import ContextVar
trace_context = ContextVar('trace_context')
```

### 8. Signal Handlers and OS Callbacks

**Issue**: Functions called by the OS (signal handlers, atexit) may not have proper context.

**Example**:
```python
@monitor()
def cleanup(signum, frame):
    # May not record properly
    save_state()

signal.signal(signal.SIGTERM, cleanup)
```

**Workaround**: Minimal monitoring in signal handlers
```python
def cleanup(signum, frame):
    try:
        save_state()  # Core functionality
    except:
        pass  # Never raise in signal handler
```

## Performance Edge Cases

### 1. Recursive Functions

**Issue**: Deep recursion can create many trace records quickly.

**Example**:
```python
@monitor()
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

factorial(1000)  # Creates 1000 trace records!
```

**Solution**: Sample recursive calls
```python
@monitor(sample_rate=0.1)  # Only trace 10% of calls
def factorial(n):
    ...
```

### 2. Tight Loops

**Issue**: Monitoring inside tight loops adds overhead.

**Bad**:
```python
for i in range(1_000_000):
    @monitor()
    def process_item(item):
        return item * 2
    
    result = process_item(i)
```

**Good**:
```python
@monitor()
def process_batch(items):
    return [item * 2 for item in items]

process_batch(range(1_000_000))
```

### 3. Large Collections as Arguments

**Issue**: Passing huge lists/dicts as arguments increases serialization time.

**Problem**:
```python
@monitor()
def process_data(huge_list):  # 1M items
    # Serializing huge_list takes time
    return len(huge_list)
```

**Solution**: Log summaries instead
```python
@monitor()
def process_data(huge_list):
    # Log metadata separately
    logger.info(f"Processing {len(huge_list)} items")
    return len(huge_list)
```

## Database Edge Cases

### 1. SQLite Lock Timeout

**Issue**: Under extreme load, SQLite may timeout on locks.

**Symptom**: "database is locked" errors

**Solution**: Automatic retry with circuit breaker protection

### 2. Retention During High Load

**Issue**: DELETE operations may slow down during write spikes.

**Impact**: Temporary database growth beyond retention window

**Resolution**: System self-corrects when load decreases

## Serialization Edge Cases

### 1. Custom __repr__ Raising Exceptions

**Issue**: Some objects have buggy __repr__ methods.

**Handled Automatically**:
```python
# If obj.__repr__() raises an exception:
# Result: "<ClassName instance>"
```

### 2. Circular References

**Issue**: Objects with circular references could cause infinite loops.

**Handled Automatically**:
```python
# SmartSerializer detects and breaks cycles:
# Result: "<dict with circular reference>"
```

### 3. Security-Sensitive Data

**Issue**: Passwords and tokens in arguments.

**Handled Automatically**:
```python
# These fields are masked:
# password, api_key, secret, token, auth
# Result: "***MASKED***"
```

## Unsupported Patterns

### 1. Monkey Patching After Decoration

**Don't Do This**:
```python
@monitor()
def original():
    return 42

# This breaks monitoring
original = lambda: 99
```

### 2. Direct Attribute Access on Decorated Functions

**Issue**: Decorated functions are wrapped.

**Problem**:
```python
@monitor()
def func():
    pass

# May not work as expected
func.custom_attribute = "value"
```

**Solution**: Use functools.wraps (already applied)

### 3. Metaclass Magic

**Issue**: Complex metaclass operations may confuse the decorator.

**Example**:
```python
class Meta(type):
    def __call__(cls, *args, **kwargs):
        # Complex manipulation here
        pass
```

**Recommendation**: Apply @monitor to regular methods, not metaclass machinery

## Best Practices for Edge Cases

### 1. Test Monitoring in Development

```python
# Verify monitoring works before production
@monitor()
def critical_function():
    pass

# Check traces were created
assert check_function_monitored(critical_function)
```

### 2. Fail Gracefully

The monitoring system never breaks your application:
- Serialization errors → Generic representation
- Queue full → Ring buffer overflow
- Database errors → Circuit breaker protection

### 3. Use Process Groups for Filtering

```python
# Exclude problematic functions
@monitor(process_group="experimental.untested")
def bleeding_edge_feature():
    pass

# Filter out in production if needed
```

### 4. Monitor at Appropriate Boundaries

```python
# Don't monitor every helper
def _helper1(x): return x + 1
def _helper2(x): return x * 2

# Monitor the public API
@monitor()
def public_api(x):
    return _helper2(_helper1(x))
```

## When NOT to Use @monitor

1. **Inside Signal Handlers**: May cause deadlocks
2. **Memory-Mapped Operations**: Can't serialize mmap objects
3. **Real-Time Audio/Video**: Overhead may cause glitches
4. **Cryptographic Operations**: Timing attacks concern
5. **GIL-Released Code**: Pure C extensions with released GIL

## Future Enhancements

### Phase 9+ Distributed Tracing
Will address:
- Cross-process correlation
- Async context propagation  
- Service mesh integration
- True parent-child relationships

### Pluggable Serializers
For specific needs:
- Binary protocols (Protocol Buffers)
- Custom object handling
- Domain-specific representations

## Summary

The observability system is robust against edge cases:
- **Graceful Degradation**: Never crashes your application
- **Automatic Handling**: Most edge cases handled transparently
- **Clear Patterns**: Known limitations have documented workarounds
- **Production Ready**: Tested with real-world edge cases

When in doubt, just add @monitor() - the system will handle it gracefully. 