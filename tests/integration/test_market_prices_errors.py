#!/usr/bin/env python3
"""
Integration tests for market price error handling and edge cases.

Tests system resilience to various error conditions.
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor, OptionsProcessor
from lib.trading.market_prices.constants import CHICAGO_TZ

class TestMarketPricesErrors:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db_path):
        """Create storage instance with temporary database."""
        return MarketPriceStorage(db_path=temp_db_path)
    
    def test_database_corruption_recovery(self, temp_db_path):
        """Test handling of corrupted database."""
        # Create initial storage and add data
        storage1 = MarketPriceStorage(db_path=temp_db_path)
        storage1.insert_or_update_futures_price(
            date(2025, 7, 15), 'TUU5', 110.5, None
        )
        
        # Corrupt the database file
        with open(temp_db_path, 'r+b') as f:
            f.seek(100)
            f.write(b'CORRUPTED_DATA_HERE')
        
        # Try to create new storage instance
        # Should handle corruption gracefully
        try:
            storage2 = MarketPriceStorage(db_path=temp_db_path)
            # If it doesn't raise, check if tables exist
            conn = storage2._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            # Should have recreated tables or handled error
        except Exception as e:
            # Should not crash the entire application
            assert "database" in str(e).lower()
    
    def test_invalid_date_formats(self, storage):
        """Test handling of invalid date formats in filenames."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Various invalid date formats
            invalid_files = [
                'Futures_2025071_1400.csv',     # Missing digit
                'Futures_20251315_1400.csv',    # Invalid month
                'Futures_20250732_1400.csv',    # Invalid day
                'Futures_20250715_2500.csv',    # Invalid hour
                'Futures_20250715_1465.csv',    # Invalid minute
                'Futures_YYYYMMDD_HHMM.csv',    # Template format
            ]
            
            for filename in invalid_files:
                filepath = Path(temp_dir) / filename
                df = pd.DataFrame({
                    'SYMBOL': ['TU'],
                    'PX_LAST': [110.5],
                    'PX_SETTLE': [110.75]
                })
                df.to_csv(filepath, index=False)
                
                # Should return None without crashing
                result = processor.process_file(filepath)
                assert result is None
    
    def test_extreme_price_values(self, storage):
        """Test handling of extreme or invalid price values."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            
            # Create file with extreme values
            df = pd.DataFrame({
                'SYMBOL': ['TU', 'FV', 'TY', 'US', 'RX'],
                'PX_LAST': [
                    999999.99,      # Very large
                    -100.5,         # Negative
                    0.0,            # Zero
                    float('inf'),   # Infinity
                    None            # Missing
                ],
                'PX_SETTLE': [110.5] * 5
            })
            df.to_csv(filepath, index=False)
            
            # Process should handle gracefully
            result = processor.process_file(filepath)
            assert result == 'current_price'
            
            # Check what was actually stored
            df_stored = storage.get_futures_by_date(date(2025, 7, 15))
            
            # Should have processed valid rows
            assert len(df_stored) >= 2  # At least the valid ones
    
    def test_concurrent_database_access(self, temp_db_path):
        """Test concurrent access to the database."""
        import threading
        import time
        
        # Create multiple storage instances
        storages = [MarketPriceStorage(db_path=temp_db_path) for _ in range(5)]
        results = [None] * 5
        errors = []
        
        def update_price(idx, symbol):
            try:
                for i in range(10):
                    storages[idx].insert_or_update_futures_price(
                        date(2025, 7, 15),
                        f'{symbol}U5',
                        110.5 + idx + i * 0.1,
                        None
                    )
                    time.sleep(0.01)
                results[idx] = 'success'
            except Exception as e:
                errors.append((idx, str(e)))
                results[idx] = 'error'
        
        # Start concurrent updates
        threads = []
        symbols = ['TU', 'FV', 'TY', 'US', 'RX']
        for i in range(5):
            t = threading.Thread(target=update_price, args=(i, symbols[i]))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All should succeed (SQLite handles concurrency)
        assert all(r == 'success' for r in results), f"Errors: {errors}"
        
        # Verify data integrity
        final_storage = MarketPriceStorage(db_path=temp_db_path)
        df = final_storage.get_futures_by_date(date(2025, 7, 15))
        assert len(df) == 5  # All symbols should be present
    
    def test_missing_required_columns(self, storage):
        """Test handling of CSV files missing required columns."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Missing PX_LAST
            filepath1 = Path(temp_dir) / 'Futures_20250715_1400.csv'
            df1 = pd.DataFrame({
                'SYMBOL': ['TU'],
                'PX_SETTLE': [110.75]
            })
            df1.to_csv(filepath1, index=False)
            
            result1 = processor.process_file(filepath1)
            assert result1 is None
            
            # Missing SYMBOL
            filepath2 = Path(temp_dir) / 'Futures_20250715_1401.csv'
            df2 = pd.DataFrame({
                'PX_LAST': [110.5],
                'PX_SETTLE': [110.75]
            })
            df2.to_csv(filepath2, index=False)
            
            result2 = processor.process_file(filepath2)
            assert result2 is None
    
    def test_empty_and_whitespace_symbols(self, storage):
        """Test handling of empty or whitespace-only symbols."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            
            df = pd.DataFrame({
                'SYMBOL': ['TU', '', '  ', None, 'FV'],
                'PX_LAST': [110.5] * 5,
                'PX_SETTLE': [110.75] * 5
            })
            df.to_csv(filepath, index=False)
            
            result = processor.process_file(filepath)
            assert result == 'current_price'
            
            # Check only valid symbols were stored
            df_stored = storage.get_futures_by_date(date(2025, 7, 15))
            symbols = df_stored['symbol'].tolist()
            
            # Should only have TU and FV with U5 suffix
            assert 'TUU5' in symbols
            assert 'FVU5' in symbols
            assert len(symbols) == 2
    
    def test_file_permissions_error(self, storage):
        """Test handling of file permission errors."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            
            # Create file
            df = pd.DataFrame({
                'SYMBOL': ['TU'],
                'PX_LAST': [110.5],
                'PX_SETTLE': [110.75]
            })
            df.to_csv(filepath, index=False)
            
            # Make file unreadable (Unix-like systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(filepath, 0o000)
                
                result = processor.process_file(filepath)
                assert result is None
                
                # Restore permissions for cleanup
                os.chmod(filepath, 0o644)
    
    def test_duplicate_symbols_in_file(self, storage):
        """Test handling of duplicate symbols in the same file."""
        processor = FuturesProcessor(storage)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            
            # Create file with duplicate symbols
            df = pd.DataFrame({
                'SYMBOL': ['TU', 'FV', 'TU', 'TU', 'FV'],
                'PX_LAST': [110.5, 108.5, 110.6, 110.7, 108.6],
                'PX_SETTLE': [110.75] * 5
            })
            df.to_csv(filepath, index=False)
            
            result = processor.process_file(filepath)
            assert result == 'current_price'
            
            # Check how duplicates were handled
            df_stored = storage.get_futures_by_date(date(2025, 7, 15))
            
            # Should have unique symbols (last value wins)
            tu_row = df_stored[df_stored['symbol'] == 'TUU5']
            assert len(tu_row) == 1
            assert tu_row.iloc[0]['current_price'] == 110.7  # Last TU value
    
    def test_network_path_handling(self, storage):
        """Test handling of network paths (if applicable)."""
        processor = FuturesProcessor(storage)
        
        # Create a path that looks like a network path
        if os.name == 'nt':  # Windows
            # Try UNC path format
            network_path = Path('//nonexistent/share/Futures_20250715_1400.csv')
        else:
            # Unix network mount
            network_path = Path('/mnt/nonexistent/Futures_20250715_1400.csv')
        
        # Should handle gracefully
        result = processor.process_file(network_path)
        assert result is None 