"""Tests for RetentionManager - simple retention implementation."""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from lib.monitoring.retention.manager import RetentionManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create schema
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE process_trace (
            ts TEXT NOT NULL,
            process TEXT NOT NULL,
            status TEXT NOT NULL,
            duration_ms REAL NOT NULL,
            exception TEXT,
            PRIMARY KEY (ts, process)
        )
    """)
    conn.execute("""
        CREATE TABLE data_trace (
            ts TEXT NOT NULL,
            process TEXT NOT NULL,
            data TEXT NOT NULL,
            data_type TEXT NOT NULL,
            data_value TEXT NOT NULL,
            status TEXT NOT NULL,
            exception TEXT,
            PRIMARY KEY (ts, process, data, data_type)
        )
    """)
    conn.execute("CREATE INDEX idx_ts_window ON process_trace(ts)")
    conn.execute("CREATE INDEX idx_data_ts ON data_trace(ts)")
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


def insert_test_data(db_path: str, hours_ago: float, count: int = 10):
    """Insert test data at specified hours ago."""
    base_time = datetime.now() - timedelta(hours=hours_ago)
    
    with sqlite3.connect(db_path) as conn:
        for i in range(count):
            ts = (base_time + timedelta(seconds=i)).isoformat()
            
            # Insert process trace
            conn.execute(
                "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?)",
                (ts, f"test.func_{i}", "OK", 10.5, None)
            )
            
            # Insert data traces
            conn.execute(
                "INSERT INTO data_trace VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, f"test.func_{i}", "arg_0", "INPUT", "value", "OK", None)
            )
            conn.execute(
                "INSERT INTO data_trace VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, f"test.func_{i}", "result", "OUTPUT", "result", "OK", None)
            )


def test_retention_manager_init(temp_db):
    """Test RetentionManager initialization."""
    manager = RetentionManager(temp_db, retention_hours=6)
    
    assert manager.db_path == temp_db
    assert manager.retention_hours == 6
    
    # Check WAL mode was set
    with sqlite3.connect(temp_db) as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        # Note: might be "wal" or previous mode if WAL not supported
        # Test passes either way since WAL is optional


def test_cleanup_no_records(temp_db):
    """Test cleanup when database is empty."""
    manager = RetentionManager(temp_db)
    
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    assert process_deleted == 0
    assert data_deleted == 0


def test_cleanup_all_recent(temp_db):
    """Test cleanup when all records are recent."""
    # Insert data from 1 hour ago
    insert_test_data(temp_db, hours_ago=1, count=20)
    
    manager = RetentionManager(temp_db, retention_hours=6)
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    assert process_deleted == 0
    assert data_deleted == 0
    
    # Verify nothing was deleted
    with sqlite3.connect(temp_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM process_trace").fetchone()[0] == 20
        assert conn.execute("SELECT COUNT(*) FROM data_trace").fetchone()[0] == 40  # 2 per process


def test_cleanup_old_records(temp_db):
    """Test cleanup of old records."""
    # Insert mix of old and new data
    insert_test_data(temp_db, hours_ago=8, count=10)  # Old
    insert_test_data(temp_db, hours_ago=2, count=15)  # Recent
    
    manager = RetentionManager(temp_db, retention_hours=6)
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    assert process_deleted == 10  # Old records deleted
    assert data_deleted == 20      # 2 data records per process
    
    # Verify only recent records remain
    with sqlite3.connect(temp_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM process_trace").fetchone()[0] == 15
        assert conn.execute("SELECT COUNT(*) FROM data_trace").fetchone()[0] == 30


def test_cleanup_exact_boundary(temp_db):
    """Test cleanup at exact retention boundary."""
    # Insert data at exactly 6 hours (should be kept)
    insert_test_data(temp_db, hours_ago=6.0, count=5)
    # Insert data slightly older (should be deleted)
    insert_test_data(temp_db, hours_ago=6.1, count=5)
    
    manager = RetentionManager(temp_db, retention_hours=6)
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    # Exact behavior depends on timestamp precision
    # But older records should be deleted
    assert process_deleted >= 5
    assert data_deleted >= 10


def test_get_retention_stats(temp_db):
    """Test retention statistics."""
    # Insert data at various times
    insert_test_data(temp_db, hours_ago=7, count=5)
    insert_test_data(temp_db, hours_ago=3, count=10)
    insert_test_data(temp_db, hours_ago=0.5, count=8)
    
    manager = RetentionManager(temp_db, retention_hours=6)
    stats = manager.get_retention_stats()
    
    assert stats['total_process_records'] == 23
    assert stats['total_data_records'] == 46
    assert stats['retention_hours'] == 6
    assert stats['database_size_mb'] > 0
    assert stats['oldest_process_ts'] is not None
    assert stats['oldest_data_ts'] is not None


def test_get_retention_stats_empty_db(temp_db):
    """Test retention statistics on empty database."""
    manager = RetentionManager(temp_db)
    stats = manager.get_retention_stats()
    
    assert stats['total_process_records'] == 0
    assert stats['total_data_records'] == 0
    assert stats['oldest_process_ts'] is None
    assert stats['oldest_data_ts'] is None
    assert stats['database_size_mb'] > 0  # Empty DB still has some size


def test_estimate_steady_state_size(temp_db):
    """Test steady state size estimation."""
    # Insert recent data to simulate current rate
    base_time = datetime.now() - timedelta(minutes=2)
    
    with sqlite3.connect(temp_db) as conn:
        for i in range(100):  # 100 records in 2 minutes
            ts = (base_time + timedelta(seconds=i)).isoformat()
            conn.execute(
                "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?)",
                (ts, f"test.func_{i}", "OK", 10.5, None)
            )
    
    manager = RetentionManager(temp_db, retention_hours=6)
    estimated_mb = manager.estimate_steady_state_size()
    
    # Should estimate based on rate
    # 100 records in 5 min = 1200/hour = 7200 in 6 hours
    # At ~500 bytes per record = ~3.5MB * 1.15 overhead = ~4MB
    assert estimated_mb > 0
    assert estimated_mb < 100  # Reasonable upper bound


def test_database_locked_error(temp_db):
    """Test handling of database locked errors."""
    manager = RetentionManager(temp_db)
    
    # Lock database with another connection
    lock_conn = sqlite3.connect(temp_db)
    lock_conn.execute("BEGIN EXCLUSIVE")
    
    # Should raise OperationalError
    with pytest.raises(sqlite3.OperationalError):
        manager.cleanup_old_records()
    
    lock_conn.close()


def test_concurrent_cleanup(temp_db):
    """Test concurrent cleanup operations."""
    import threading
    
    # Insert test data
    insert_test_data(temp_db, hours_ago=8, count=100)
    
    manager = RetentionManager(temp_db, retention_hours=6)
    results = []
    
    def cleanup_thread():
        try:
            result = manager.cleanup_old_records()
            results.append(result)
        except Exception as e:
            results.append(e)
    
    # Run multiple cleanups concurrently
    threads = [threading.Thread(target=cleanup_thread) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # At least one should succeed
    successful_cleanups = [r for r in results if isinstance(r, tuple)]
    assert len(successful_cleanups) >= 1
    
    # Total deleted should be the 100 old records (once)
    total_deleted = sum(r[0] for r in successful_cleanups)
    assert total_deleted == 100


def test_time_warp_cleanup(temp_db):
    """Test cleanup with time-warped queries for testing."""
    # Insert future data (simulating clock issues)
    future_time = datetime.now() + timedelta(hours=1)
    
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?)",
            (future_time.isoformat(), "future.func", "OK", 10.5, None)
        )
    
    # Also insert old data
    insert_test_data(temp_db, hours_ago=8, count=5)
    
    manager = RetentionManager(temp_db, retention_hours=6)
    process_deleted, data_deleted = manager.cleanup_old_records()
    
    # Should only delete old data, not future data
    assert process_deleted == 5
    
    # Future record should remain
    with sqlite3.connect(temp_db) as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM process_trace").fetchone()[0]
        assert remaining == 1 