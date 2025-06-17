"""Demo showing circuit breaker protecting the observability system."""

import time
import sqlite3
from pathlib import Path

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer
)
from lib.monitoring.circuit_breaker import CircuitBreaker


def simulate_database_failure():
    """Demo: Simulating database failures and recovery."""
    print("\n=== Circuit Breaker Demo ===\n")
    
    # Start observability
    db_path = "logs/circuit_breaker_demo.db"
    Path(db_path).parent.mkdir(exist_ok=True)
    
    start_observability_writer(
        db_path=db_path,
        batch_size=5,
        drain_interval=0.1
    )
    
    @monitor()
    def business_function(x):
        """Simulated business logic."""
        return x ** 2
    
    # Phase 1: Normal operation
    print("Phase 1: Normal operation - generating 10 records")
    for i in range(10):
        result = business_function(i)
        print(f"  Result: {result}")
    
    time.sleep(0.5)  # Let writes complete
    
    # Get initial stats
    from lib.monitoring.decorators.monitor import _batch_writer
    if _batch_writer:
        stats = _batch_writer.get_stats()
        print(f"\nInitial stats:")
        print(f"  Records written: {stats['total_written']}")
        print(f"  Circuit breaker state: {stats['circuit_breaker']['state']}")
        print(f"  Circuit breaker calls: {stats['circuit_breaker']['total_calls']}")
    
    # Phase 2: Simulate failures by injecting errors
    print("\n\nPhase 2: Simulating database failures")
    
    # Create a custom circuit breaker to demonstrate
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=2)
    
    def failing_operation():
        raise Exception("Simulated database error")
    
    # Trigger failures
    for i in range(5):
        try:
            cb.call(failing_operation)
        except Exception as e:
            print(f"  Attempt {i+1}: {type(e).__name__}: {e}")
    
    # Show circuit breaker state
    cb_stats = cb.get_stats()
    print(f"\nCircuit breaker after failures:")
    print(f"  State: {cb_stats['state']}")
    print(f"  Failures: {cb_stats['total_failures']}")
    print(f"  Circuit opened count: {cb_stats['circuit_opened_count']}")
    
    # Phase 3: Recovery
    print("\n\nPhase 3: Waiting for recovery...")
    time.sleep(2.5)
    
    def successful_operation():
        return "Success!"
    
    # Try again after timeout
    try:
        result = cb.call(successful_operation)
        print(f"  Recovery attempt 1: {result}")
        result = cb.call(successful_operation)
        print(f"  Recovery attempt 2: {result}")
    except Exception as e:
        print(f"  Recovery failed: {e}")
    
    # Final state
    cb_stats = cb.get_stats()
    print(f"\nFinal circuit breaker state:")
    print(f"  State: {cb_stats['state']}")
    print(f"  Total calls: {cb_stats['total_calls']}")
    print(f"  Successes: {cb_stats['total_successes']}")
    print(f"  Failures: {cb_stats['total_failures']}")
    
    # Clean up
    stop_observability_writer()
    
    # Show database contents
    print("\n\nDatabase contents:")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM process_trace")
        count = cursor.fetchone()[0]
        print(f"  Total process traces: {count}")
        
        cursor.execute("SELECT process, status, duration_ms FROM process_trace ORDER BY ts DESC LIMIT 5")
        print("\n  Recent traces:")
        for row in cursor.fetchall():
            print(f"    {row[0]} - {row[1]} - {row[2]:.2f}ms")
        
        conn.close()
    except Exception as e:
        print(f"  Error reading database: {e}")


def test_writer_circuit_breaker():
    """Test the actual writer's circuit breaker."""
    print("\n\n=== Testing Writer Circuit Breaker ===\n")
    
    # Create a database that will fail
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Start writer  
    from lib.monitoring.writers.sqlite_writer import BatchWriter
    from lib.monitoring.decorators.monitor import get_observability_queue
    
    queue = get_observability_queue()
    writer = BatchWriter(
        db_path=db_path,
        queue=queue,
        batch_size=2,
        drain_interval=0.05
    )
    
    # Configure for faster demo
    writer.circuit_breaker.failure_threshold = 2
    writer.circuit_breaker.timeout_seconds = 1
    
    print(f"Writer circuit breaker config:")
    print(f"  Failure threshold: {writer.circuit_breaker.failure_threshold}")
    print(f"  Timeout: {writer.circuit_breaker.timeout_seconds}s")
    
    # Delete the database to cause write failures
    import os
    os.unlink(db_path)
    
    # Start the writer
    writer.start()
    
    # Generate some records
    @monitor()
    def test_func(n):
        return n * 2
    
    print("\nGenerating records (database deleted, should fail):")
    for i in range(10):
        test_func(i)
        time.sleep(0.1)
    
    # Check circuit breaker state
    time.sleep(0.5)
    stats = writer.get_stats()
    cb_stats = stats['circuit_breaker']
    
    print(f"\nWriter circuit breaker stats:")
    print(f"  State: {cb_stats['state']}")
    print(f"  Total calls: {cb_stats['total_calls']}")
    print(f"  Failures: {cb_stats['total_failures']}")
    print(f"  Circuit opened: {cb_stats['circuit_opened_count']}")
    
    # Stop writer
    writer.stop()
    
    # Clean up
    try:
        os.unlink(db_path)
    except:
        pass


if __name__ == "__main__":
    simulate_database_failure()
    test_writer_circuit_breaker() 