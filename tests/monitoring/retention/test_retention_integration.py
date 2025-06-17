"""Integration tests for retention system with real observability data."""

import pytest
import tempfile
import time
import os
from datetime import datetime, timedelta

from lib.monitoring.decorators.monitor import (
    monitor, start_observability_writer, stop_observability_writer,
    get_observability_queue
)
from lib.monitoring.retention import RetentionManager, RetentionController


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


def test_retention_with_observability_system(temp_db_path):
    """Test retention integrated with full observability system."""
    # Clear any existing queue
    queue = get_observability_queue()
    queue.clear()
    
    # Start observability with retention enabled
    start_observability_writer(
        db_path=temp_db_path,
        batch_size=10,
        drain_interval=0.05,
        retention_hours=0.1,  # 6 minutes for testing
        retention_enabled=True
    )
    
    try:
        # Generate some data
        @monitor()
        def test_function(x):
            return x * 2
        
        # Create records over time
        for i in range(20):
            test_function(i)
            time.sleep(0.01)
        
        # Wait for data to be written
        time.sleep(0.2)
        
        # Manually insert old data to test retention
        import sqlite3
        old_time = datetime.now() - timedelta(hours=1)
        
        with sqlite3.connect(temp_db_path) as conn:
            # Insert old records
            for i in range(10):
                ts = (old_time + timedelta(seconds=i)).isoformat()
                conn.execute(
                    "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (ts, f"old.func_{i}", "OK", 10.5, None, 0, 0, 0, None, None)
                )
        
        # Force a cleanup cycle
        manager = RetentionManager(temp_db_path, retention_hours=0.1)
        process_deleted, data_deleted = manager.cleanup_old_records()
        
        # Should have deleted the old records
        assert process_deleted == 10
        
        # Recent records should remain
        with sqlite3.connect(temp_db_path) as conn:
            recent_count = conn.execute(
                "SELECT COUNT(*) FROM process_trace WHERE process LIKE '%test_function%'"
            ).fetchone()[0]
            assert recent_count >= 19  # At least most recent records
            
    finally:
        stop_observability_writer()


def test_retention_steady_state(temp_db_path):
    """Test retention reaches steady state size."""
    # Start without automatic retention
    start_observability_writer(
        db_path=temp_db_path,
        batch_size=10,
        drain_interval=0.05,
        retention_enabled=False
    )
    
    try:
        @monitor()
        def steady_function(n):
            return sum(range(n))
        
        # Generate initial data
        for i in range(50):
            steady_function(10)
        time.sleep(0.2)  # Let writes complete
        
        # Check initial database size
        initial_size = os.path.getsize(temp_db_path)
        print(f"Initial DB size: {initial_size} bytes")
        
        # Now start retention with very short period  
        manager = RetentionManager(temp_db_path, retention_hours=0.01)  # 36 seconds
        
        # Clean up old data manually once
        deleted = manager.cleanup_old_records()
        print(f"Initial cleanup: {deleted}")
        
        # Generate more data to see steady state
        for i in range(100):
            steady_function(10)
            if i % 20 == 0:
                time.sleep(0.1)  # Let some age
                deleted = manager.cleanup_old_records()
                if deleted[0] > 0:
                    print(f"Cleanup {i}: deleted {deleted}")
        
        # Final cleanup
        time.sleep(0.05)
        final_deleted = manager.cleanup_old_records()
        print(f"Final cleanup: {final_deleted}")
        
        # Check final state
        final_size = os.path.getsize(temp_db_path)
        stats = manager.get_retention_stats()
        
        print(f"Final DB size: {final_size} bytes")
        print(f"Retention stats: {stats}")
        
        # Database should not grow unbounded
        # With steady state, size should stabilize (allowing for some overhead)
        assert final_size < initial_size * 3  # Should not triple in size
        assert stats['total_process_records'] > 0  # Should have some records

    finally:
        stop_observability_writer()


def test_retention_error_handling(temp_db_path):
    """Test retention handles errors gracefully."""
    # Create initial database
    start_observability_writer(
        db_path=temp_db_path,
        retention_enabled=False
    )
    
    @monitor()
    def error_function():
        raise ValueError("Test error")
    
    # Generate mix of success and errors
    for i in range(10):
        try:
            if i % 3 == 0:
                error_function()
            else:
                @monitor()
                def success_function():
                    return "success"
                success_function()
        except:
            pass
    
    # Wait for writes
    time.sleep(0.2)
    stop_observability_writer()
    
    # Now test retention with potential corruption
    manager = RetentionManager(temp_db_path, retention_hours=6)
    
    # Should handle cleanup even with error records
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    # Should complete without raising
    stats = manager.get_retention_stats()
    assert 'total_process_records' in stats
    assert 'database_size_mb' in stats 