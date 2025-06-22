# Simple Plan to Achieve 10/10 Robustness

## Current Score: 8/10

### What's Missing (2 points)

1. **Memory Pressure Handling** (0.5 points)
2. **Basic Error Recovery** (0.5 points)  
3. **Performance Documentation** (0.5 points)
4. **Unsupported Pattern Documentation** (0.5 points)

## Simple Solutions (1 day of work)

### 1. Memory Pressure Testing (2 hours)
```python
# tests/monitoring/observability/test_memory_pressure.py
import resource
import gc

def test_monitor_under_memory_pressure():
    """Test monitoring when system is low on memory."""
    # Limit memory to 100MB
    resource.setrlimit(resource.RLIMIT_AS, (100*1024*1024, -1))
    
    @monitor()
    def memory_hungry():
        # Try to allocate large object
        try:
            data = "x" * (50 * 1024 * 1024)  # 50MB
            return len(data)
        except MemoryError:
            return -1
    
    result = memory_hungry()
    # Should gracefully handle memory error
    assert result == -1 or result == 52428800

def test_serializer_with_huge_objects():
    """Test serializer doesn't cause OOM with huge objects."""
    huge_list = list(range(10_000_000))  # ~80MB
    
    serializer = SmartSerializer(max_repr=1000)
    result = serializer.serialize(huge_list)
    
    # Should use lazy serialization
    assert "[list with 10000000 items]" in result
    assert len(result) < 100  # Not the full representation
```

### 2. Basic Circuit Breaker (3 hours)
```python
# lib/monitoring/circuit_breaker.py
import time
from typing import Optional

class CircuitBreaker:
    """Simple circuit breaker for SQLite writer."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
    
    def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure_time > self.timeout:
                # Try to close the circuit
                self.is_open = False
                self.failure_count = 0
            else:
                # Circuit still open
                raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            # Success - reset failure count
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                
            raise

# Use in SQLite writer:
# self.circuit_breaker.call(self._execute_batch, batch)
```

### 3. Performance Guide (1 hour)
```markdown
# Performance Guide

## When to Use Sampling

| Scenario | Recommended Sampling | Rationale |
|----------|---------------------|-----------|
| Hot loops (>1000 calls/sec) | 0.01 (1%) | Avoid queue overflow |
| Regular functions (10-1000 calls/sec) | 0.1 (10%) | Balance visibility/performance |
| Critical functions (<10 calls/sec) | 1.0 (100%) | Full visibility needed |

## Performance Limits

- **SQLite Writer**: ~1,089 ops/sec sustained
- **Queue Capacity**: 10,000 + 50,000 overflow
- **Overhead**: <50µs per call (without I/O)

## When to Consider Alternatives

If you need >5,000 ops/sec sustained:
1. Use sampling (`@monitor(sample_rate=0.1)`)
2. Consider ClickHouse or TimescaleDB
3. Use separate observability infrastructure

## Example High-Performance Setup

```python
# For hot paths
@monitor(sample_rate=0.01, capture=dict(args=False, result=False))
def hot_function():
    pass

# For critical paths  
@monitor(sample_rate=1.0, capture=dict(args=True, result=True))
def critical_function():
    pass
```
```

### 4. Unsupported Patterns Doc (1 hour)
```markdown
# Unsupported Patterns

## What We Don't Support (By Design)

### 1. Metaclass Methods
```python
# NOT SUPPORTED
class Meta(type):
    @monitor()  # Won't work correctly
    def __new__(cls, name, bases, attrs):
        pass
```
**Workaround**: Log manually inside metaclass methods

### 2. Slots with Descriptors
```python
# LIMITED SUPPORT
class Optimized:
    __slots__ = ['x', 'y']
    
    @property
    @monitor()  # May not capture correctly
    def computed(self):
        return self.x + self.y
```
**Workaround**: Monitor the methods that call the property

### 3. Coroutines That Never Complete
```python
# WILL LEAK MEMORY
@monitor()
async def infinite_loop():
    while True:
        await asyncio.sleep(1)
        # Never completes - record never written
```
**Workaround**: Use sampling or monitor inside the loop

### 4. Dynamic Function Creation
```python
# NOT AUTOMATICALLY MONITORED
def make_function():
    def inner():
        pass
    return monitor()(inner)  # Must manually wrap
```

## Supported Patterns

✅ Regular functions
✅ Async functions  
✅ Generators (sync and async)
✅ Class methods, static methods
✅ Most decorators stacking
✅ Exception handling
✅ Multithreading
✅ Multiprocessing (each process has own queue)
```

## Implementation Checklist (1 day)

- [ ] Add memory pressure tests (2 hours)
- [ ] Implement basic circuit breaker (3 hours)
- [ ] Write performance guide (1 hour)
- [ ] Document unsupported patterns (1 hour)
- [ ] Update robustness analysis doc (30 min)

## Why This Gets Us to 10/10

1. **Memory Pressure** ✓ We test it and document behavior
2. **Error Recovery** ✓ Circuit breaker prevents cascading failures
3. **Performance** ✓ Clear limits and guidance
4. **Edge Cases** ✓ Documented what we don't support

## What We're NOT Doing (Intentionally)

- ❌ Complex distributed tracing (YAGNI for now)
- ❌ Custom memory allocator (overengineering)
- ❌ Supporting every Python pattern (impossible)
- ❌ Fixing SQLite performance (use sampling instead)

## Result

A robust system that:
- Handles 99% of real use cases
- Fails gracefully for the 1%
- Has clear documentation
- Doesn't pretend to do things it can't 