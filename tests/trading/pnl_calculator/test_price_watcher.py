"""Tests for price file watcher."""

import unittest
from unittest.mock import Mock, patch, call
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import pytz

from lib.trading.pnl_calculator.price_watcher import PriceFileWatcher, PriceFileHandler
from watchdog.events import FileCreatedEvent, FileModifiedEvent


class TestPriceFileHandler(unittest.TestCase):
    """Test the price file handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chicago_tz = pytz.timezone('America/Chicago')
        self.mock_processor = Mock()
        self.handler = PriceFileHandler(self.mock_processor, self.chicago_tz)
        
    def test_is_price_file_valid(self):
        """Test price file validation with valid file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.csv', 
            prefix='market_prices_20250115_1400',
            delete=False
        ) as tmp:
            tmp.write("test data")
            tmp_path = Path(tmp.name)
        
        try:
            self.assertTrue(self.handler._is_price_file(tmp_path))
        finally:
            tmp_path.unlink()
    
    def test_is_price_file_invalid(self):
        """Test price file validation with invalid files."""
        # Wrong prefix
        self.assertFalse(self.handler._is_price_file(Path("other_file.csv")))
        
        # Wrong extension
        self.assertFalse(self.handler._is_price_file(Path("market_prices_20250115_1400.txt")))
        
        # Non-existent file
        self.assertFalse(self.handler._is_price_file(Path("market_prices_20250115_1400.csv")))
    
    def test_get_file_time(self):
        """Test extracting timestamp from filename."""
        # Valid filename
        path = Path("market_prices_20250115_1400.csv")
        file_time = self.handler._get_file_time(path)
        self.assertIsNotNone(file_time)
        self.assertEqual(file_time.year, 2025)
        self.assertEqual(file_time.month, 1)
        self.assertEqual(file_time.day, 15)
        self.assertEqual(file_time.hour, 14)
        self.assertEqual(file_time.minute, 0)
        
        # Invalid filename
        path = Path("invalid_file.csv")
        file_time = self.handler._get_file_time(path)
        self.assertIsNone(file_time)
    
    def test_is_in_valid_window(self):
        """Test time window validation."""
        # 2pm window (1:45-2:30)
        dt_2pm = self.chicago_tz.localize(datetime(2025, 1, 15, 14, 0))
        self.assertTrue(self.handler._is_in_valid_window(dt_2pm))
        
        dt_145pm = self.chicago_tz.localize(datetime(2025, 1, 15, 13, 45))
        self.assertTrue(self.handler._is_in_valid_window(dt_145pm))
        
        dt_230pm = self.chicago_tz.localize(datetime(2025, 1, 15, 14, 30))
        self.assertTrue(self.handler._is_in_valid_window(dt_230pm))
        
        # 4pm window (3:45-4:30)
        dt_4pm = self.chicago_tz.localize(datetime(2025, 1, 15, 16, 0))
        self.assertTrue(self.handler._is_in_valid_window(dt_4pm))
        
        # Outside windows
        dt_3pm = self.chicago_tz.localize(datetime(2025, 1, 15, 15, 0))
        self.assertFalse(self.handler._is_in_valid_window(dt_3pm))
        
        dt_5pm = self.chicago_tz.localize(datetime(2025, 1, 15, 17, 0))
        self.assertFalse(self.handler._is_in_valid_window(dt_5pm))
    
    def test_on_created_valid_file(self):
        """Test handling file creation event with valid file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            prefix='market_prices_20250115_1400',
            delete=False
        ) as tmp:
            tmp.write("test data")
            tmp_path = Path(tmp.name)
        
        try:
            # Create event
            event = FileCreatedEvent(str(tmp_path))
            
            # Handle event
            self.handler.on_created(event)
            
            # Verify processor was called
            self.mock_processor.assert_called_once_with(tmp_path)
            
        finally:
            tmp_path.unlink()
    
    def test_on_created_duplicate_file(self):
        """Test handling duplicate file (already processed)."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            prefix='market_prices_20250115_1400',
            delete=False
        ) as tmp:
            tmp.write("test data")
            tmp_path = Path(tmp.name)
        
        try:
            # Mark as already processed
            file_key = f"{tmp_path.name}:{tmp_path.stat().st_mtime}"
            self.handler.processed_files.add(file_key)
            
            # Create event
            event = FileCreatedEvent(str(tmp_path))
            
            # Handle event
            self.handler.on_created(event)
            
            # Verify processor was NOT called
            self.mock_processor.assert_not_called()
            
        finally:
            tmp_path.unlink()


class TestPriceFileWatcher(unittest.TestCase):
    """Test the price file watcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_processor = Mock()
        self.watcher = PriceFileWatcher([self.test_dir], self.mock_processor)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.watcher.is_running:
            self.watcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_start_stop(self):
        """Test starting and stopping the watcher."""
        # Start watcher
        self.watcher.start()
        self.assertTrue(self.watcher.is_running)
        
        # Stop watcher
        self.watcher.stop()
        self.assertFalse(self.watcher.is_running)
    
    def test_process_existing_files(self):
        """Test processing existing files on startup."""
        # Create test files
        file1 = Path(self.test_dir) / "market_prices_20250115_1400.csv"
        file2 = Path(self.test_dir) / "market_prices_20250115_1600.csv"
        file3 = Path(self.test_dir) / "market_prices_20250115_1500.csv"  # 3pm - should be ignored
        
        for f in [file1, file2, file3]:
            f.write_text("test data")
        
        # Start watcher (which processes existing files)
        self.watcher.start()
        
        # Verify only valid time window files were processed
        self.assertEqual(self.mock_processor.call_count, 2)
        
        # Check that the right files were processed
        processed_files = [call[0][0].name for call in self.mock_processor.call_args_list]
        self.assertIn("market_prices_20250115_1400.csv", processed_files)
        self.assertIn("market_prices_20250115_1600.csv", processed_files)
        self.assertNotIn("market_prices_20250115_1500.csv", processed_files)


if __name__ == '__main__':
    unittest.main() 