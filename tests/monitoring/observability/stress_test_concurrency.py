"""Concurrency stress tests for the observability system.

This module tests the monitor decorator and queue system under extreme concurrent load
to identify race conditions, performance bottlenecks, and data integrity issues.
"""

import asyncio
import time
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any
import statistics
import random

from lib.monitoring.decorators.monitor import (
    monitor, get_observability_queue, start_observability_writer, stop_observability_writer
)
from lib.monitoring.queues import ObservabilityRecord


class ConcurrencyStressTest:
    """Framework for stress testing concurrent operations."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.errors: List[Exception] = []
        self.lock = threading.Lock()
    
    def record_result(self, test_name: str, metric: str, value: Any):
        """Thread-safe result recording."""
        with self.lock:
            if test_name not in self.results:
                self.results[test_name] = {}
            if metric not in self.results[test_name]:
                self.results[test_name][metric] = []
            self.results[test_name][metric].append(value)
    
    def record_error(self, error: Exception):
        """Thread-safe error recording."""
        with self.lock:
            self.errors.append(error)
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "="*80)
        print("CONCURRENCY STRESS TEST RESULTS")
        print("="*80)
        
        for test_name, metrics in self.results.items():
            print(f"\n{test_name}:")
            for metric, values in metrics.items():
                if values and isinstance(values[0], (int, float)):
                    avg = statistics.mean(values)
                    median = statistics.median(values)
                    min_val = min(values)
                    max_val = max(values)
                    print(f"  {metric}:")
                    print(f"    Mean: {avg:.3f}, Median: {median:.3f}")
                    print(f"    Min: {min_val:.3f}, Max: {max_val:.3f}")
                else:
                    print(f"  {metric}: {len(values)} items")
        
        if self.errors:
            print(f"\nERRORS: {len(self.errors)} errors occurred")
            for i, error in enumerate(self.errors[:5]):  # Show first 5
                print(f"  {i+1}. {type(error).__name__}: {str(error)}")


def test_high_frequency_calls():
    """Test 1: High-frequency function calls from multiple threads."""
    print("\n=== TEST 1: High Frequency Parallel Calls ===")
    
    @monitor()
    def quick_function(x: int) -> int:
        """Minimal function for max throughput testing."""
        return x * 2
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    num_threads = 20
    calls_per_thread = 1000
    
    def worker(thread_id: int):
        """Worker thread that makes many rapid calls."""
        start = time.perf_counter()
        try:
            for i in range(calls_per_thread):
                result = quick_function(i)
                if result != i * 2:
                    stress_test.record_error(
                        ValueError(f"Thread {thread_id}: Expected {i*2}, got {result}")
                    )
        except Exception as e:
            stress_test.record_error(e)
        
        duration = time.perf_counter() - start
        stress_test.record_result("high_frequency", "thread_duration_sec", duration)
        stress_test.record_result("high_frequency", "calls_per_sec", calls_per_thread / duration)
    
    # Run test
    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for future in futures:
            future.result()
    
    total_duration = time.perf_counter() - start_time
    
    # Verify results
    stats = queue.get_queue_stats()
    expected_records = num_threads * calls_per_thread
    actual_records = stats['metrics']['normal_enqueued']
    
    print(f"Total calls: {expected_records:,}")
    print(f"Duration: {total_duration:.3f} seconds")
    print(f"Overall throughput: {expected_records/total_duration:,.0f} calls/sec")
    print(f"Records captured: {actual_records:,}")
    print(f"Data integrity: {'PASS' if actual_records == expected_records else 'FAIL'}")
    
    stress_test.record_result("high_frequency", "total_calls", expected_records)
    stress_test.record_result("high_frequency", "overall_throughput", expected_records/total_duration)
    stress_test.record_result("high_frequency", "data_integrity", actual_records == expected_records)
    
    return stress_test


def test_mixed_sync_async():
    """Test 2: Mixed synchronous and asynchronous operations."""
    print("\n\n=== TEST 2: Mixed Sync/Async Operations ===")
    
    @monitor()
    def sync_operation(n: int) -> int:
        """Synchronous CPU-bound operation."""
        total = 0
        for i in range(n):
            total += i
        return total
    
    @monitor()
    async def async_operation(n: int) -> int:
        """Asynchronous I/O-bound operation."""
        await asyncio.sleep(0.001)  # Simulate I/O
        return n * n
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    async def async_worker(worker_id: int, iterations: int):
        """Async worker mixing sync and async calls."""
        try:
            for i in range(iterations):
                # Alternate between sync and async
                if i % 2 == 0:
                    result = sync_operation(100)
                else:
                    result = await async_operation(i)
        except Exception as e:
            stress_test.record_error(e)
    
    def sync_worker(worker_id: int, iterations: int):
        """Sync worker making sync calls."""
        try:
            for i in range(iterations):
                result = sync_operation(100)
        except Exception as e:
            stress_test.record_error(e)
    
    async def run_mixed_test():
        """Run both sync and async workers concurrently."""
        start = time.perf_counter()
        
        # Create async tasks
        async_tasks = []
        for i in range(10):
            task = asyncio.create_task(async_worker(i, 50))
            async_tasks.append(task)
        
        # Run sync workers in thread pool
        with ThreadPoolExecutor(max_workers=10) as executor:
            sync_futures = [executor.submit(sync_worker, i, 50) for i in range(10, 20)]
            
            # Wait for all async tasks
            await asyncio.gather(*async_tasks)
            
            # Wait for sync workers
            for future in sync_futures:
                future.result()
        
        duration = time.perf_counter() - start
        return duration
    
    # Run test
    duration = asyncio.run(run_mixed_test())
    
    stats = queue.get_queue_stats()
    total_records = stats['metrics']['normal_enqueued']
    
    print(f"Mixed workload duration: {duration:.3f} seconds")
    print(f"Total records: {total_records:,}")
    print(f"Records/sec: {total_records/duration:,.0f}")
    
    stress_test.record_result("mixed_sync_async", "duration", duration)
    stress_test.record_result("mixed_sync_async", "total_records", total_records)
    stress_test.record_result("mixed_sync_async", "throughput", total_records/duration)
    
    return stress_test


def test_queue_contention():
    """Test 3: Queue contention under extreme load."""
    print("\n\n=== TEST 3: Queue Contention Test ===")
    
    @monitor()
    def generate_data(size: int) -> list:
        """Generate data of varying sizes to stress serialization."""
        return [random.random() for _ in range(size)]
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    # Track queue size over time
    queue_sizes = []
    monitoring_active = threading.Event()
    monitoring_active.set()
    
    def queue_monitor():
        """Monitor queue size during test."""
        while monitoring_active.is_set():
            stats = queue.get_queue_stats()
            size = stats['normal_queue_size']
            queue_sizes.append(size)
            time.sleep(0.01)  # Sample every 10ms
    
    def load_generator(worker_id: int, duration: float):
        """Generate varying load patterns."""
        start = time.perf_counter()
        call_count = 0
        
        while time.perf_counter() - start < duration:
            # Vary data size to create different serialization loads
            size = random.choice([10, 100, 1000, 10000])
            try:
                generate_data(size)
                call_count += 1
            except Exception as e:
                stress_test.record_error(e)
        
        stress_test.record_result("queue_contention", "calls_per_worker", call_count)
    
    # Start queue monitor
    monitor_thread = threading.Thread(target=queue_monitor)
    monitor_thread.start()
    
    # Run load generators
    test_duration = 5.0  # seconds
    num_workers = 50  # High contention
    
    print(f"Running {num_workers} workers for {test_duration} seconds...")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(load_generator, i, test_duration) for i in range(num_workers)]
        for future in futures:
            future.result()
    
    # Stop monitoring
    monitoring_active.clear()
    monitor_thread.join()
    
    # Analyze results
    if queue_sizes:
        max_queue_size = max(queue_sizes)
        avg_queue_size = statistics.mean(queue_sizes)
        
        print(f"Max queue size: {max_queue_size:,}")
        print(f"Avg queue size: {avg_queue_size:,.0f}")
        print(f"Queue samples: {len(queue_sizes)}")
        
        # Check for queue overflow
        overflow_threshold = 10000
        overflows = sum(1 for size in queue_sizes if size > overflow_threshold)
        print(f"Queue overflows (>{overflow_threshold}): {overflows}")
        
        stress_test.record_result("queue_contention", "max_queue_size", max_queue_size)
        stress_test.record_result("queue_contention", "avg_queue_size", avg_queue_size)
        stress_test.record_result("queue_contention", "overflow_count", overflows)
    
    return stress_test


def test_error_handling_under_load():
    """Test 4: Error handling and recovery under concurrent load."""
    print("\n\n=== TEST 4: Error Handling Under Load ===")
    
    error_counter = threading.Lock()
    error_count = 0
    
    @monitor()
    def unreliable_function(fail_rate: float = 0.1) -> str:
        """Function that fails randomly."""
        nonlocal error_count
        if random.random() < fail_rate:
            with error_counter:
                error_count += 1
            raise ValueError(f"Random failure #{error_count}")
        return "success"
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    def worker(worker_id: int, iterations: int):
        """Worker that handles errors gracefully."""
        successes = 0
        failures = 0
        
        for i in range(iterations):
            try:
                result = unreliable_function(fail_rate=0.2)  # 20% failure rate
                successes += 1
            except ValueError:
                failures += 1
            except Exception as e:
                stress_test.record_error(e)
        
        stress_test.record_result("error_handling", "successes", successes)
        stress_test.record_result("error_handling", "failures", failures)
    
    # Run test
    num_workers = 20
    iterations_per_worker = 100
    
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker, i, iterations_per_worker) for i in range(num_workers)]
        for future in futures:
            future.result()
    duration = time.perf_counter() - start
    
    # Verify error records
    stats = queue.get_queue_stats()
    error_records = stats['metrics']['error_enqueued']
    total_records = stats['metrics']['normal_enqueued']
    
    print(f"Total operations: {num_workers * iterations_per_worker}")
    print(f"Error count: {error_count}")
    print(f"Error records in queue: {error_records}")
    print(f"Total records: {total_records}")
    print(f"Duration: {duration:.3f} seconds")
    
    # Verify all errors were captured
    print(f"Error capture integrity: {'PASS' if error_records >= error_count else 'FAIL'}")
    
    stress_test.record_result("error_handling", "error_capture_integrity", error_records >= error_count)
    
    return stress_test


def test_memory_stress():
    """Test 5: Memory allocation patterns under concurrent load."""
    print("\n\n=== TEST 5: Memory Allocation Stress ===")
    
    @monitor()
    def memory_intensive_operation(size_mb: int) -> int:
        """Allocate and process large amounts of memory."""
        # Allocate approximately size_mb of memory
        data = bytearray(size_mb * 1024 * 1024)
        # Do some work to prevent optimization
        checksum = sum(data[::1000])
        return checksum
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    def worker(worker_id: int):
        """Worker that performs memory-intensive operations."""
        sizes = [1, 5, 10, 20]  # MB
        
        for size in sizes:
            try:
                start = time.perf_counter()
                result = memory_intensive_operation(size)
                duration = time.perf_counter() - start
                stress_test.record_result("memory_stress", f"duration_{size}mb", duration)
            except Exception as e:
                stress_test.record_error(e)
                stress_test.record_result("memory_stress", "allocation_failure", size)
    
    # Run with limited workers to avoid OOM
    num_workers = 5
    
    print(f"Running {num_workers} memory-intensive workers...")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker, i) for i in range(num_workers)]
        for future in futures:
            future.result()
    
    # Check queue behavior under memory pressure
    stats = queue.get_queue_stats()
    print(f"Records queued: {stats['metrics']['normal_enqueued']}")
    print(f"Queue errors: {stats['metrics'].get('enqueue_errors', 0)}")
    
    return stress_test


async def test_async_generator_concurrency():
    """Test 6: Concurrent async generator monitoring."""
    print("\n\n=== TEST 6: Async Generator Concurrency ===")
    
    @monitor()
    async def data_stream(stream_id: int, count: int):
        """Simulate async data stream."""
        for i in range(count):
            await asyncio.sleep(0.001)  # Simulate I/O
            yield f"stream_{stream_id}_item_{i}"
    
    stress_test = ConcurrencyStressTest()
    queue = get_observability_queue()
    queue.clear()
    
    async def consume_stream(stream_id: int):
        """Consume items from async generator."""
        items = []
        try:
            async for item in data_stream(stream_id, 10):
                items.append(item)
        except Exception as e:
            stress_test.record_error(e)
        
        stress_test.record_result("async_gen_concurrency", "items_consumed", len(items))
        return items
    
    # Run multiple concurrent streams
    num_streams = 20
    
    start = time.perf_counter()
    tasks = [consume_stream(i) for i in range(num_streams)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.perf_counter() - start
    
    # Count successful streams
    successful = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"Concurrent streams: {num_streams}")
    print(f"Successful streams: {successful}")
    print(f"Duration: {duration:.3f} seconds")
    
    # Each stream should create 1 OK record
    stats = queue.get_queue_stats()
    records = stats['metrics']['normal_enqueued']
    print(f"Generator records: {records}")
    
    stress_test.record_result("async_gen_concurrency", "successful_streams", successful)
    stress_test.record_result("async_gen_concurrency", "duration", duration)
    
    return stress_test


def run_all_stress_tests():
    """Run all concurrency stress tests."""
    print("=" * 80)
    print("OBSERVABILITY SYSTEM CONCURRENCY STRESS TESTS")
    print("=" * 80)
    
    # Initialize observability writer
    start_observability_writer(db_path="logs/stress_test.db", batch_size=500)
    
    all_results = []
    
    try:
        # Run each test
        all_results.append(test_high_frequency_calls())
        all_results.append(test_mixed_sync_async())
        all_results.append(test_queue_contention())
        all_results.append(test_error_handling_under_load())
        all_results.append(test_memory_stress())
        
        # Run async test
        async_test = asyncio.run(test_async_generator_concurrency())
        all_results.append(async_test)
        
    finally:
        # Stop writer
        stop_observability_writer()
    
    # Print combined summary
    print("\n" * 2)
    combined = ConcurrencyStressTest()
    for test in all_results:
        combined.results.update(test.results)
        combined.errors.extend(test.errors)
    
    combined.print_summary()
    
    # Overall health check
    print("\n" + "="*80)
    print("OVERALL SYSTEM HEALTH")
    print("="*80)
    
    total_errors = len(combined.errors)
    if total_errors == 0:
        print("✅ All stress tests passed without errors")
    else:
        print(f"⚠️  {total_errors} errors detected during stress testing")
    
    # Performance summary
    if "high_frequency" in combined.results:
        throughput = combined.results["high_frequency"]["overall_throughput"][0]
        print(f"\n📊 Peak throughput: {throughput:,.0f} operations/second")


if __name__ == "__main__":
    import os
    os.environ["MONITOR_QUIET"] = "1"  # Reduce output noise
    run_all_stress_tests() 