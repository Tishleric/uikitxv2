"""Integration tests for @monitor decorator with complete pipeline - Phase 6"""

import pytest
import time
import tempfile
import sqlite3
import os
from datetime import datetime

from lib.monitoring.decorators import monitor, start_observability_writer, stop_observability_writer, get_observability_queue
from lib.monitoring.queues import ObservabilityQueue
import numpy as np
import pandas as pd


@pytest.fixture
def temp_db():
    """Create a temporary database file"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    try:
        os.unlink(path)
        # Also remove WAL and SHM files if they exist
        for ext in ['-wal', '-shm']:
            wal_path = path + ext
            if os.path.exists(wal_path):
                os.unlink(wal_path)
    except:
        pass


@pytest.fixture
def clean_queue():
    """Ensure we have a clean queue for each test"""
    # Get the queue and drain it
    queue = get_observability_queue()
    while True:
        batch = queue.drain(1000)
        if not batch:
            break
    yield queue


class TestMonitorIntegration:
    """Test suite for complete monitor decorator integration"""
    
    def test_basic_function_monitoring(self, temp_db, clean_queue):
        """Test basic function monitoring through complete pipeline"""
        # Start the writer
        writer = start_observability_writer(temp_db)
        
        # Define and call a monitored function
        @monitor(process_group="test.basic")
        def add_numbers(a, b):
            """Add two numbers"""
            return a + b
        
        result = add_numbers(5, 3)
        assert result == 8
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify data in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check process trace
        cursor.execute("SELECT process, status, duration_ms FROM process_trace WHERE process LIKE '%add_numbers%'")
        row = cursor.fetchone()
        assert row is not None
        process, status, duration = row
        assert "add_numbers" in process
        assert status == "OK"
        assert duration > 0
        
        # Check data traces
        cursor.execute("SELECT data, data_type, data_value FROM data_trace WHERE process LIKE '%add_numbers%' ORDER BY data")
        rows = cursor.fetchall()
        assert len(rows) == 3  # arg_0, arg_1, result
        
        # Verify arguments
        assert rows[0][0] == "arg_0"  # data name
        assert rows[0][1] == "INPUT"   # data type
        assert rows[0][2] == "5"       # value
        
        assert rows[1][0] == "arg_1"
        assert rows[1][1] == "INPUT"
        assert rows[1][2] == "3"
        
        # Verify result
        assert rows[2][0] == "result"
        assert rows[2][1] == "OUTPUT"
        assert rows[2][2] == "8"
        
        conn.close()
        stop_observability_writer()
    
    def test_exception_handling(self, temp_db, clean_queue):
        """Test exception handling and error recording"""
        writer = start_observability_writer(temp_db)
        
        @monitor(process_group="test.errors")
        def failing_function(msg):
            """Function that always fails"""
            raise ValueError(f"Intentional error: {msg}")
        
        # Call should raise but record error
        with pytest.raises(ValueError, match="Intentional error: test123"):
            failing_function("test123")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify error in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check process trace
        cursor.execute("SELECT process, status, exception FROM process_trace WHERE status = 'ERR'")
        row = cursor.fetchone()
        assert row is not None
        process, status, exception = row
        assert "failing_function" in process
        assert status == "ERR"
        assert "ValueError: Intentional error: test123" in exception
        assert "Traceback" in exception
        
        conn.close()
        stop_observability_writer()
    
    def test_complex_data_types(self, temp_db, clean_queue):
        """Test monitoring with complex data types"""
        writer = start_observability_writer(temp_db)
        
        @monitor(process_group="test.complex", capture={"args": True, "result": True})
        def process_data(arr, df, config):
            """Process complex data"""
            return {
                "sum": float(arr.sum()),
                "mean": float(df["value"].mean()),
                "status": config["status"]
            }
        
        # Create test data
        arr = np.array([1, 2, 3, 4, 5])
        df = pd.DataFrame({"value": [10, 20, 30]})
        config = {"status": "active", "threshold": 0.5}
        
        result = process_data(arr, df, config)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check data traces
        cursor.execute("SELECT data, data_value FROM data_trace WHERE process LIKE '%process_data%' ORDER BY data")
        rows = cursor.fetchall()
        
        # Find specific values
        data_dict = {row[0]: row[1] for row in rows}
        
        # Check array was serialized
        assert "arg_0" in data_dict
        assert "[ndarray int" in data_dict["arg_0"]
        
        # Check DataFrame was serialized
        assert "arg_1" in data_dict
        assert "[DataFrame" in data_dict["arg_1"]
        
        # Check config was serialized
        assert "arg_2" in data_dict
        assert "'status': 'active'" in data_dict["arg_2"]
        
        # Check result
        assert "result" in data_dict
        assert "'sum': 15.0" in data_dict["result"]
        assert "'mean': 20.0" in data_dict["result"]
        
        conn.close()
        stop_observability_writer()
    
    def test_sampling_rate(self, temp_db, clean_queue):
        """Test sampling rate functionality"""
        writer = start_observability_writer(temp_db)
        
        call_count = 0
        
        @monitor(process_group="test.sampling", sample_rate=0.5)
        def sampled_function():
            """Function with 50% sampling"""
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Call function many times
        for _ in range(100):
            sampled_function()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check that not all calls were recorded
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM process_trace WHERE process LIKE '%sampled_function%'")
        recorded_count = cursor.fetchone()[0]
        
        # With 50% sampling, we expect roughly 40-60 records (allowing for randomness)
        assert 30 <= recorded_count <= 70
        assert recorded_count < 100  # Definitely less than all calls
        
        conn.close()
        stop_observability_writer()
    
    def test_sensitive_data_masking(self, temp_db, clean_queue):
        """Test sensitive field masking"""
        writer = start_observability_writer(temp_db)
        
        @monitor(process_group="test.security", sensitive_fields=("password", "api_key", "token"))
        def login(username, password, api_key=None):
            """Sensitive function"""
            return {"token": "secret123", "user": username}
        
        result = login("john", "mypassword", api_key="sk-12345")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify masking in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data, data_value FROM data_trace WHERE process LIKE '%login%'")
        rows = cursor.fetchall()
        
        data_dict = {row[0]: row[1] for row in rows}
        
        # Password should be masked
        assert "arg_1" in data_dict
        assert data_dict["arg_1"] == "'***REDACTED***'"
        
        # API key should be masked
        assert "api_key" in data_dict
        assert data_dict["api_key"] == "'***REDACTED***'"
        
        # Username should NOT be masked
        assert "arg_0" in data_dict
        assert data_dict["arg_0"] == "'john'"
        
        # Token in result should be masked
        assert "result" in data_dict
        assert "'token': '***REDACTED***'" in data_dict["result"]
        assert "'user': 'john'" in data_dict["result"]
        
        conn.close()
        stop_observability_writer()
    
    def test_queue_warning_threshold(self, temp_db, clean_queue, capsys):
        """Test queue warning threshold"""
        writer = start_observability_writer(temp_db)
        
        @monitor(process_group="test.queue", queue_warning_threshold=5)
        def fast_function(i):
            return i * 2
        
        # Stop writer to let queue build up
        stop_observability_writer()
        
        # Call function many times to fill queue
        for i in range(10):
            fast_function(i)
        
        # Check for warning in output
        captured = capsys.readouterr()
        assert "[MONITOR] WARNING: Queue size" in captured.out
        assert "exceeds threshold 5" in captured.out
    
    def test_capture_options(self, temp_db, clean_queue):
        """Test different capture options"""
        writer = start_observability_writer(temp_db)
        
        @monitor(process_group="test.capture", capture={"args": False, "result": True})
        def partial_capture(x, y):
            """Only capture result, not args"""
            return x * y
        
        result = partial_capture(6, 7)
        assert result == 42
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Should have result but no args
        cursor.execute("SELECT data FROM data_trace WHERE process LIKE '%partial_capture%'")
        rows = cursor.fetchall()
        
        data_names = [row[0] for row in rows]
        assert "result" in data_names
        assert "arg_0" not in data_names
        assert "arg_1" not in data_names
        
        conn.close()
        stop_observability_writer()
    
    def test_performance_overhead(self, clean_queue):
        """Test that monitoring overhead is acceptable"""
        # Function without monitoring
        def unmonitored_function():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        # Function with monitoring (no writer for pure overhead test)
        @monitor(process_group="test.perf")
        def monitored_function():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        # Time unmonitored
        start = time.perf_counter()
        for _ in range(100):
            unmonitored_function()
        unmonitored_time = time.perf_counter() - start
        
        # Time monitored
        start = time.perf_counter()
        for _ in range(100):
            monitored_function()
        monitored_time = time.perf_counter() - start
        
        # Calculate overhead
        overhead_ms = ((monitored_time - unmonitored_time) / 100) * 1000
        
        # Should be less than 0.05ms (50µs) per call
        assert overhead_ms < 0.05, f"Overhead too high: {overhead_ms:.3f}ms per call"
        
        # Drain queue to clean up
        while True:
            batch = clean_queue.drain(1000)
            if not batch:
                break 