"""Test that observability system uses the new observatory.db database"""

import os
import sqlite3
import tempfile
import shutil
from pathlib import Path

import pytest

from lib.monitoring.decorators.monitor import monitor, start_observatory_writer, stop_observatory_writer, get_observatory_queue
from lib.monitoring.writers import SQLiteWriter


class TestObservatoryDatabase:
    """Test database separation for Observatory dashboard"""
    
    def test_default_database_path(self):
        """Test that default database is observatory.db"""
        writer = SQLiteWriter()
        assert writer.db_path == "logs/observatory.db"
    
    def test_custom_database_path(self):
        """Test that custom database path works"""
        custom_path = "custom/path/test.db"
        writer = SQLiteWriter(db_path=custom_path)
        assert writer.db_path == custom_path
    
    def test_observatory_db_creation(self, tmp_path):
        """Test that observatory.db is created with correct schema"""
        # Create temporary directory
        db_dir = tmp_path / "logs"
        db_dir.mkdir()
        db_path = str(db_dir / "observatory.db")
        
        # Create writer
        writer = SQLiteWriter(db_path=db_path)
        
        # Verify database exists
        assert Path(db_path).exists()
        
        # Verify schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "process_trace" in tables
        assert "data_trace" in tables
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_process_ts" in indexes
        assert "idx_data_process" in indexes
        assert "idx_ts_window" in indexes
        
        # Check view exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = {row[0] for row in cursor.fetchall()}
        assert "parent_child_traces" in views
        
        conn.close()
    
    def test_monitor_decorator_uses_observatory_db(self, tmp_path):
        """Test that @monitor decorator writes to observatory.db by default"""
        # Create temporary logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        # Change to temporary directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Start writer (should create observatory.db)
            writer = start_observatory_writer()
            
            # Define and call a monitored function
            @monitor(process_group="test")
            def test_function(x, y):
                return x + y
            
            result = test_function(1, 2)
            assert result == 3
            
            # Stop writer to flush
            stop_observatory_writer()
            
            # Verify observatory.db was created
            assert (logs_dir / "observatory.db").exists()
            
            # Verify data was written
            conn = sqlite3.connect(str(logs_dir / "observatory.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM process_trace")
            count = cursor.fetchone()[0]
            assert count > 0
            conn.close()
            
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_no_legacy_observability_db(self, tmp_path):
        """Test that we don't create the old observability.db"""
        # Create temporary logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        # Change to temporary directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Start writer
            writer = start_observatory_writer()
            
            # Define and call a monitored function
            @monitor(process_group="test")
            def test_function():
                return "test"
            
            test_function()
            
            # Stop writer
            stop_observatory_writer()
            
            # Verify only observatory.db exists, not observability.db
            assert (logs_dir / "observatory.db").exists()
            assert not (logs_dir / "observability.db").exists()
            
        finally:
            os.chdir(original_cwd) 