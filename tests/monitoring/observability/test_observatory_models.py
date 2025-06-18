"""Test Observatory dashboard data models"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
import pytest
import pandas as pd

from apps.dashboards.observatory.models import (
    ObservatoryDataService, MetricsAggregator, TraceAnalyzer
)
from lib.monitoring.decorators.monitor import monitor, start_observability_writer, stop_observability_writer


class TestObservatoryModels:
    """Test Observatory data models and services"""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing"""
        db_path = str(tmp_path / "test_observatory.db")
        
        # Create test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create schema (matching SQLiteWriter)
        cursor.execute("""
            CREATE TABLE process_trace (
                ts TEXT NOT NULL,
                process TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                exception TEXT,
                thread_id INTEGER DEFAULT 0,
                call_depth INTEGER DEFAULT 0,
                start_ts_us INTEGER DEFAULT 0,
                PRIMARY KEY (ts, process)
            )
        """)
        
        cursor.execute("""
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
        
        # Create the parent_child_traces view
        cursor.execute("""
            CREATE VIEW parent_child_traces AS
            SELECT 
                p1.ts as parent_ts,
                p1.process as parent_process,
                p2.ts as child_ts,
                p2.process as child_process,
                p2.call_depth - p1.call_depth as depth_diff,
                0 as time_diff_ms
            FROM process_trace p1, process_trace p2
            WHERE p1.thread_id = p2.thread_id
            AND p2.call_depth = p1.call_depth + 1
        """)
        
        # Insert test data
        now = datetime.now()
        test_data = []
        
        # Success traces
        for i in range(10):
            ts = (now - timedelta(minutes=i)).isoformat()
            test_data.append((
                ts,
                f"test.module.function_{i % 3}",
                "OK",
                10.5 + i,
                None,
                1,
                1,
                int((now - timedelta(minutes=i)).timestamp() * 1_000_000)
            ))
        
        # Error traces
        for i in range(3):
            ts = (now - timedelta(minutes=20+i)).isoformat()
            test_data.append((
                ts,
                f"test.module.error_function",
                "ERR",
                50.5,
                "Test exception traceback",
                1,
                1,
                int((now - timedelta(minutes=20+i)).timestamp() * 1_000_000)
            ))
        
        cursor.executemany(
            "INSERT INTO process_trace VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_data
        )
        
        # Insert data traces
        data_traces = []
        for trace in test_data[:5]:  # First 5 traces
            ts = trace[0]
            process = trace[1]
            status = trace[2]
            exception = trace[4]
            
            # Input data
            data_traces.append((
                ts, process, "arg_0", "INPUT", "test_value", status, exception
            ))
            # Output data
            data_traces.append((
                ts, process, "result", "OUTPUT", "42", status, exception
            ))
        
        cursor.executemany(
            "INSERT INTO data_trace VALUES (?, ?, ?, ?, ?, ?, ?)",
            data_traces
        )
        
        conn.commit()
        conn.close()
        
        yield db_path
    
    def test_observatory_data_service_init(self, temp_db):
        """Test ObservatoryDataService initialization"""
        service = ObservatoryDataService(db_path=temp_db)
        assert service.db_path == temp_db
        assert os.path.exists(temp_db)
    
    def test_get_trace_data(self, temp_db):
        """Test getting paginated trace data"""
        service = ObservatoryDataService(db_path=temp_db)
        
        # Get first page
        df, total = service.get_trace_data(page=1, page_size=5)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5  # Should get 5 rows
        assert total == 10  # Total should be 10 (5 traces * 2 data types each)
        
        # Check columns
        expected_columns = ['process', 'data', 'data_type', 'data_value', 
                          'timestamp', 'status', 'exception']
        assert list(df.columns) == expected_columns
    
    def test_get_trace_data_with_filters(self, temp_db):
        """Test getting trace data with filters"""
        service = ObservatoryDataService(db_path=temp_db)
        
        # Filter by status
        df, total = service.get_trace_data(status_filter="OK")
        assert all(df['status'] == 'OK')
        
        # Filter by process
        df, total = service.get_trace_data(process_filter="function_0")
        assert all('function_0' in proc for proc in df['process'])
    
    def test_get_process_metrics(self, temp_db):
        """Test getting aggregated process metrics"""
        service = ObservatoryDataService(db_path=temp_db)
        
        df = service.get_process_metrics(hours=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'process' in df.columns
        assert 'call_count' in df.columns
        assert 'avg_duration_ms' in df.columns
        assert 'error_rate' in df.columns
    
    def test_get_recent_errors(self, temp_db):
        """Test getting recent error traces"""
        service = ObservatoryDataService(db_path=temp_db)
        
        df = service.get_recent_errors(limit=10)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3  # We inserted 3 errors
        assert all(df['exception'].notna())
    
    def test_get_system_stats(self, temp_db):
        """Test getting system statistics"""
        service = ObservatoryDataService(db_path=temp_db)
        
        stats = service.get_system_stats()
        
        assert isinstance(stats, dict)
        assert stats['total_traces'] == 13  # 10 OK + 3 ERR
        assert stats['total_data_points'] == 10  # 5 traces * 2 data points each
        assert 'error_rate' in stats
        assert 'db_size_mb' in stats
        assert stats['db_size_mb'] > 0
    
    def test_metrics_aggregator(self, temp_db):
        """Test MetricsAggregator functionality"""
        service = ObservatoryDataService(db_path=temp_db)
        aggregator = MetricsAggregator(service)
        
        # Test top slow functions
        df = aggregator.get_top_slow_functions(limit=5)
        assert isinstance(df, pd.DataFrame)
    
    def test_trace_analyzer(self, temp_db):
        """Test TraceAnalyzer functionality"""
        service = ObservatoryDataService(db_path=temp_db)
        analyzer = TraceAnalyzer(service)
        
        # Test stale process detection
        stale = analyzer.detect_stale_processes(expected_interval_seconds=600)  # 10 minutes
        assert isinstance(stale, list)
        # Should detect the error traces as stale (20+ minutes old)
        assert len(stale) > 0
    
    def test_integration_with_real_monitor(self, tmp_path):
        """Test with real @monitor decorator writing to database"""
        # Create temporary database
        db_path = str(tmp_path / "real_observatory.db")
        
        # Start observability writer
        writer = start_observability_writer(db_path=db_path)
        
        try:
            # Define and call monitored functions
            @monitor(process_group="test.integration")
            def successful_function(x, y):
                return x + y
            
            @monitor(process_group="test.integration")
            def failing_function():
                raise ValueError("Test error")
            
            # Call functions
            result = successful_function(10, 20)
            assert result == 30
            
            with pytest.raises(ValueError):
                failing_function()
            
            # Stop writer to flush
            stop_observability_writer()
            
            # Now query with ObservatoryDataService
            service = ObservatoryDataService(db_path=db_path)
            
            # Check system stats
            stats = service.get_system_stats()
            assert stats['total_traces'] >= 2  # At least our 2 function calls
            
            # Check trace data
            df, total = service.get_trace_data()
            assert total > 0
            assert len(df) > 0
            
            # Check errors
            errors = service.get_recent_errors()
            assert len(errors) >= 1  # At least our failing function
            
        finally:
            # Ensure writer is stopped
            try:
                stop_observability_writer()
            except:
                pass 