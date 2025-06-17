#!/usr/bin/env python3
"""Benchmark script for Phase 8 performance optimizations."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import time
import statistics
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from lib.monitoring import monitor
from lib.monitoring.decorators.monitor import get_observability_queue, start_observability_writer
from lib.monitoring.performance import get_metadata_cache


# Test functions with different data types
@monitor(process_group="benchmark.primitives")
def process_primitives(x: int, y: float, name: str, active: bool) -> Dict[str, Any]:
    """Test with primitive types (fast path)."""
    return {
        "sum": x + y,
        "name": name.upper(),
        "status": "active" if active else "inactive"
    }


@monitor(process_group="benchmark.collections")
def process_collections(items: List[int], mapping: Dict[str, float]) -> float:
    """Test with simple collections (fast path)."""
    total = sum(items)
    for key, value in mapping.items():
        total += value
    return total


@monitor(process_group="benchmark.complex")
def process_complex_data(df: pd.DataFrame, array: np.ndarray) -> Dict[str, Any]:
    """Test with complex data types (requires full serialization)."""
    return {
        "df_shape": df.shape,
        "array_mean": float(array.mean()),
        "df_columns": list(df.columns)
    }


@monitor(process_group="benchmark.large")
def process_large_string(text: str) -> int:
    """Test with large string (lazy serialization)."""
    return len(text)


@monitor(process_group="benchmark.nested")
def outer_function(n: int) -> int:
    """Test nested function calls."""
    result = 0
    for i in range(n):
        result += inner_function(i)
    return result


@monitor(process_group="benchmark.nested")
def inner_function(x: int) -> int:
    """Inner function for nested calls."""
    return x * 2


def benchmark_function(func, args, kwargs, iterations: int = 1000) -> Dict[str, float]:
    """Benchmark a function with multiple iterations."""
    import os
    
    # Enable quiet mode for benchmarking
    os.environ["MONITOR_QUIET"] = "1"
    
    times = []
    
    # Warmup
    for _ in range(10):
        func(*args, **kwargs)
    
    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)  # Convert to microseconds
    
    return {
        "mean_us": statistics.mean(times),
        "median_us": statistics.median(times),
        "stdev_us": statistics.stdev(times) if len(times) > 1 else 0,
        "min_us": min(times),
        "max_us": max(times)
    }


def main():
    """Run performance benchmarks."""
    print("Phase 8 Performance Benchmark\n" + "=" * 50)
    
    # Initialize writer
    writer = start_observability_writer("logs/benchmark_phase8.db")
    
    # Clear the queue to start fresh
    queue = get_observability_queue()
    queue.clear()
    print("Cleared queue for fresh benchmark run\n")
    
    # Test data
    large_string = "x" * 50000  # 50KB string
    df = pd.DataFrame({
        "col1": range(100),
        "col2": np.random.rand(100),
        "col3": ["test"] * 100
    })
    array = np.random.rand(100, 100)
    
    # Benchmark scenarios
    scenarios = [
        ("Primitives (fast path)", process_primitives, 
         (42, 3.14, "test", True), {}),
        
        ("Simple collections (fast path)", process_collections,
         ([1, 2, 3, 4, 5], {"a": 1.1, "b": 2.2, "c": 3.3}), {}),
        
        ("Complex data (full serialization)", process_complex_data,
         (df, array), {}),
        
        ("Large string (lazy serialization)", process_large_string,
         (large_string,), {}),
        
        ("Nested calls (10 inner)", outer_function,
         (10,), {}),
    ]
    
    # Run benchmarks
    results = []
    for name, func, args, kwargs in scenarios:
        print(f"\nBenchmarking: {name}")
        stats = benchmark_function(func, args, kwargs, iterations=1000)
        
        print(f"  Mean: {stats['mean_us']:.2f} µs")
        print(f"  Median: {stats['median_us']:.2f} µs")
        print(f"  Std Dev: {stats['stdev_us']:.2f} µs")
        print(f"  Min: {stats['min_us']:.2f} µs")
        print(f"  Max: {stats['max_us']:.2f} µs")
        
        results.append({
            "scenario": name,
            **stats
        })
    
    # Check overhead target
    print("\n" + "=" * 50)
    print("OVERHEAD ANALYSIS:")
    print("-" * 50)
    
    target_us = 50
    for result in results:
        overhead_ok = result['median_us'] < target_us
        status = "✅ PASS" if overhead_ok else "❌ FAIL"
        print(f"{result['scenario']:<40} {result['median_us']:>8.2f} µs  {status}")
    
    # Queue statistics
    queue = get_observability_queue()
    queue_stats = queue.get_queue_stats()
    metrics = queue_stats['metrics']
    
    print("\n" + "=" * 50)
    print("QUEUE STATISTICS:")
    print("-" * 50)
    print(f"Normal queue size: {queue_stats['normal_queue_size']}")
    print(f"Error queue size: {queue_stats['error_queue_size']}")
    print(f"Overflow buffer size: {queue_stats['overflow_buffer_size']}")
    print(f"Total normal records: {metrics['normal_enqueued']}")
    print(f"Total error records: {metrics['error_enqueued']}")
    print(f"Records overflowed: {metrics['overflowed']}")
    print(f"Records recovered: {metrics['recovered']}")
    
    # Cache statistics
    cache = get_metadata_cache()
    cache_stats = cache.get_stats()
    
    print("\n" + "=" * 50)
    print("CACHE STATISTICS:")
    print("-" * 50)
    print(f"Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"Hit rate: {cache_stats['hit_rate']:.2%}")
    print(f"Hits: {cache_stats['hits']}")
    print(f"Misses: {cache_stats['misses']}")
    
    # Give writer time to flush
    time.sleep(0.5)
    
    # Check if all scenarios met target
    all_passed = all(r['median_us'] < target_us for r in results)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL BENCHMARKS PASSED - Overhead < 50µs target")
    else:
        print("❌ SOME BENCHMARKS FAILED - Optimization needed")
    
    # Cleanup
    writer.stop()


if __name__ == "__main__":
    main() 