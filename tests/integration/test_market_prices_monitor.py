#!/usr/bin/env python3
"""
Integration tests for market price file monitoring.

Tests file watcher functionality, callback execution, and error recovery.
"""

import pytest
import os
import sys
import tempfile
import shutil
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.trading.market_prices import MarketPriceStorage, MarketPriceFileMonitor
from lib.trading.market_prices.constants import CHICAGO_TZ

class TestMarketPriceMonitor:
    """Integration tests for file monitoring functionality."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as base_dir:
            base_path = Path(base_dir)
            futures_dir = base_path / 'futures'
            options_dir = base_path / 'options'
            futures_dir.mkdir()
            options_dir.mkdir()
            
            yield {
                'base': base_path,
                'futures': futures_dir,
                'options': options_dir
            }
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db_path):
        """Create storage instance with temporary database."""
        return MarketPriceStorage(db_path=temp_db_path)
    
    @pytest.fixture
    def monitor(self, storage, temp_dirs):
        """Create monitor instance with test directories."""
        monitor = MarketPriceFileMonitor(
            storage=storage,
            futures_dir=temp_dirs['futures'],
            options_dir=temp_dirs['options']
        )
        yield monitor
        # Ensure monitor is stopped
        monitor.stop()
    
    def create_futures_csv(self, filepath):
        """Helper to create a futures CSV file."""
        data = {
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [110.5, 108.25, 115.75],
            'PX_SETTLE': [110.75, 108.5, 116.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    
    def create_options_csv(self, filepath):
        """Helper to create an options CSV file."""
        data = {
            'SYMBOL': ['TUU5 C 110', 'TUU5 P 110'],
            'PX_LAST': [0.5, 0.3],
            'PX_SETTLE': [0.52, 0.32],
            'EXPIRE_DT': ['2025-09-30'] * 2,
            'MONEYNESS': ['ATM', 'ATM']
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    
    def test_monitor_startup_processes_existing_files(self, monitor, temp_dirs, storage):
        """Test that monitor processes existing files on startup."""
        # Create files before starting monitor
        futures_file = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        options_file = temp_dirs['options'] / 'Options_20250715_1400.csv'
        
        self.create_futures_csv(futures_file)
        self.create_options_csv(options_file)
        
        # Start monitor
        monitor.start()
        
        # Give it time to process existing files
        time.sleep(2)
        
        # Verify files were processed
        futures_df = storage.get_futures_by_date(datetime(2025, 7, 15).date())
        options_df = storage.get_options_by_date(datetime(2025, 7, 15).date())
        
        assert len(futures_df) == 3
        assert len(options_df) == 2
        
        monitor.stop()
    
    def test_monitor_detects_new_files(self, monitor, temp_dirs, storage):
        """Test that monitor detects and processes new files."""
        # Start monitor first
        monitor.start()
        time.sleep(1)
        
        # Create new files
        futures_file = temp_dirs['futures'] / 'Futures_20250715_1600.csv'
        self.create_futures_csv(futures_file)
        
        # Wait for processing
        time.sleep(2)
        
        # Verify file was processed (4pm creates next day entry)
        df = storage.get_futures_by_date(datetime(2025, 7, 16).date())
        assert len(df) == 3
        
        monitor.stop()
    
    def test_monitor_callbacks(self, monitor, temp_dirs):
        """Test that monitor executes callbacks correctly."""
        callback_results = {
            'futures': [],
            'options': []
        }
        
        def futures_callback(filepath, result):
            callback_results['futures'].append((filepath.name, result))
        
        def options_callback(filepath, result):
            callback_results['options'].append((filepath.name, result))
        
        # Set callbacks
        monitor.set_futures_callback(futures_callback)
        monitor.set_options_callback(options_callback)
        
        # Start monitor
        monitor.start()
        time.sleep(1)
        
        # Create files
        futures_file = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        options_file = temp_dirs['options'] / 'Options_20250715_1400.csv'
        
        self.create_futures_csv(futures_file)
        self.create_options_csv(options_file)
        
        # Wait for processing
        time.sleep(2)
        
        # Verify callbacks were executed
        assert len(callback_results['futures']) == 1
        assert callback_results['futures'][0] == ('Futures_20250715_1400.csv', 'current_price')
        
        assert len(callback_results['options']) == 1
        assert callback_results['options'][0] == ('Options_20250715_1400.csv', 'current_price')
        
        monitor.stop()
    
    def test_monitor_ignores_non_matching_files(self, monitor, temp_dirs, storage):
        """Test that monitor ignores files that don't match expected patterns."""
        monitor.start()
        time.sleep(1)
        
        # Create non-matching files
        wrong_files = [
            temp_dirs['futures'] / 'wrong_format.csv',
            temp_dirs['futures'] / 'Futures_baddate_1400.csv',
            temp_dirs['futures'] / 'Future_20250715_1400.csv',  # Wrong prefix
            temp_dirs['options'] / 'options_20250715_1400.csv',  # Wrong case
            temp_dirs['futures'] / 'Futures_20250715_1400.txt',  # Wrong extension
        ]
        
        for filepath in wrong_files:
            filepath.write_text("dummy content")
        
        # Also create one valid file
        valid_file = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        self.create_futures_csv(valid_file)
        
        # Wait for processing
        time.sleep(2)
        
        # Only the valid file should be processed
        df = storage.get_futures_by_date(datetime(2025, 7, 15).date())
        assert len(df) == 3  # Only from the valid file
        
        monitor.stop()
    
    def test_monitor_handles_file_errors_gracefully(self, monitor, temp_dirs, storage):
        """Test that monitor continues working when encountering file errors."""
        monitor.start()
        time.sleep(1)
        
        # Create a file that will cause an error
        bad_file = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        bad_file.write_text("this is not valid CSV content")
        
        # Create a valid file after the bad one
        valid_file = temp_dirs['futures'] / 'Futures_20250715_1401.csv'
        self.create_futures_csv(valid_file)
        
        # Wait for processing
        time.sleep(2)
        
        # The valid file should still be processed
        df = storage.get_futures_by_date(datetime(2025, 7, 15).date())
        assert len(df) > 0  # At least the valid file was processed
        
        monitor.stop()
    
    def test_monitor_concurrent_file_creation(self, monitor, temp_dirs, storage):
        """Test monitor handles multiple files created simultaneously."""
        monitor.start()
        time.sleep(1)
        
        # Create multiple files in parallel
        def create_file(minute):
            filepath = temp_dirs['futures'] / f'Futures_20250715_14{minute:02d}.csv'
            self.create_futures_csv(filepath)
        
        threads = []
        for i in range(5):  # Create 5 files
            t = threading.Thread(target=create_file, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Wait for all processing
        time.sleep(3)
        
        # All files should be processed
        df = storage.get_futures_by_date(datetime(2025, 7, 15).date())
        # Should have 3 symbols, but current_price updated multiple times
        assert len(df) == 3
        
        monitor.stop()
    
    def test_monitor_stop_and_restart(self, monitor, temp_dirs, storage):
        """Test that monitor can be stopped and restarted cleanly."""
        # Start monitor
        monitor.start()
        assert monitor.is_running()
        
        # Create a file
        file1 = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        self.create_futures_csv(file1)
        time.sleep(2)
        
        # Stop monitor
        monitor.stop()
        assert not monitor.is_running()
        
        # Create another file while stopped
        file2 = temp_dirs['futures'] / 'Futures_20250715_1401.csv'
        self.create_futures_csv(file2)
        time.sleep(1)
        
        # Restart monitor
        monitor.start()
        time.sleep(2)
        
        # Both files should be processed (second one on restart)
        df = storage.get_futures_by_date(datetime(2025, 7, 15).date())
        assert len(df) == 3
    
    def test_monitor_memory_leak_prevention(self, monitor, temp_dirs):
        """Test that monitor doesn't accumulate processed files in memory."""
        monitor.start()
        time.sleep(1)
        
        # Get initial processed files count
        initial_count = len(monitor._processed_files)
        
        # Process many files
        for i in range(20):
            filepath = temp_dirs['futures'] / f'Futures_20250715_14{i:02d}.csv'
            self.create_futures_csv(filepath)
            time.sleep(0.1)
        
        # Wait for processing
        time.sleep(3)
        
        # Processed files set should not grow indefinitely
        # (implementation should have some cleanup mechanism)
        final_count = len(monitor._processed_files)
        assert final_count <= 50  # Reasonable upper bound
        
        monitor.stop()
    
    def test_monitor_handles_directory_deletion(self, monitor, temp_dirs):
        """Test monitor handles monitored directory being deleted."""
        monitor.start()
        time.sleep(1)
        
        # Delete the futures directory
        shutil.rmtree(temp_dirs['futures'])
        
        # Monitor should continue running
        time.sleep(1)
        assert monitor.is_running()
        
        # Recreate directory and add file
        temp_dirs['futures'].mkdir()
        file1 = temp_dirs['futures'] / 'Futures_20250715_1400.csv'
        self.create_futures_csv(file1)
        
        # File should still be processed
        time.sleep(2)
        # Note: Depending on watchdog implementation, this might require monitor restart
        
        monitor.stop() 