#!/usr/bin/env python3
"""
Core integration tests for market price processing system.

Tests basic functionality, time window validation, and data integrity.
"""

import pytest
import os
import sys
import tempfile
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor, OptionsProcessor
from lib.trading.market_prices.constants import CHICAGO_TZ

class TestMarketPricesCore:
    """Core integration tests for market price processing."""
    
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
    def futures_processor(self, storage):
        """Create futures processor instance."""
        return FuturesProcessor(storage)
    
    @pytest.fixture
    def options_processor(self, storage):
        """Create options processor instance."""
        return OptionsProcessor(storage)
    
    def create_futures_csv(self, filepath, timestamp_str, symbols=None, px_last=110.5, px_settle=110.75):
        """Helper to create a futures CSV file."""
        if symbols is None:
            symbols = ['TU', 'FV', 'TY', 'US', 'RX']
        
        data = {
            'SYMBOL': symbols,
            'PX_LAST': [px_last + i * 0.1 for i in range(len(symbols))],
            'PX_SETTLE': [px_settle + i * 0.1 for i in range(len(symbols))]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
        # Update file modification time to match timestamp
        # Extract datetime from filename format: Futures_YYYYMMDD_HHMM.csv
        datetime_str = timestamp_str.replace('Futures_', '').replace('.csv', '')
        dt = datetime.strptime(datetime_str, '%Y%m%d_%H%M')
        chicago_dt = CHICAGO_TZ.localize(dt)
        timestamp = chicago_dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
    
    def create_options_csv(self, filepath, timestamp_str):
        """Helper to create an options CSV file."""
        data = {
            'SYMBOL': ['TUU5 C 110', 'TUU5 P 110', 'FVU5 C 108', 'FVU5 P 108'],
            'PX_LAST': [0.5, 0.3, 0.6, 0.4],
            'PX_SETTLE': [0.52, 0.32, 0.62, 0.42],
            'EXPIRE_DT': ['2025-09-30'] * 4,
            'MONEYNESS': ['ATM', 'ATM', 'OTM', 'OTM']
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
        # Update file modification time
        datetime_str = timestamp_str.replace('Options_', '').replace('.csv', '')
        dt = datetime.strptime(datetime_str, '%Y%m%d_%H%M')
        chicago_dt = CHICAGO_TZ.localize(dt)
        timestamp = chicago_dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
    
    def test_basic_futures_processing_2pm(self, futures_processor, storage):
        """Test basic futures processing at 2pm window."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 2pm file
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            self.create_futures_csv(filepath, filepath.name)
            
            # Process file
            result = futures_processor.process_file(filepath)
            assert result == 'current_price', f"Expected 'current_price' but got {result}"
            
            # Verify data in database
            conn = storage._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, current_price, prior_close 
                FROM futures_prices 
                WHERE trade_date = '2025-07-15'
                ORDER BY symbol
            """)
            rows = cursor.fetchall()
            conn.close()
            
            # Should have 5 symbols with U5 suffix
            assert len(rows) == 5
            
            # Verify U5 suffix was added
            for row in rows:
                assert row[0].endswith('U5'), f"Symbol {row[0]} doesn't have U5 suffix"
            
            # Verify current_price is populated, prior_close is NULL
            for row in rows:
                assert row[1] is not None, f"Current price is NULL for {row[0]}"
                assert row[2] is None, f"Prior close should be NULL for {row[0]}"
    
    def test_basic_futures_processing_4pm(self, futures_processor, storage):
        """Test basic futures processing at 4pm window."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 4pm file
            filepath = Path(temp_dir) / 'Futures_20250715_1600.csv'
            self.create_futures_csv(filepath, filepath.name)
            
            # Process file
            result = futures_processor.process_file(filepath)
            assert result == 'prior_close', f"Expected 'prior_close' but got {result}"
            
            # Verify data in database - should create entry for NEXT day
            conn = storage._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, current_price, prior_close 
                FROM futures_prices 
                WHERE trade_date = '2025-07-16'
                ORDER BY symbol
            """)
            rows = cursor.fetchall()
            conn.close()
            
            # Should have 5 symbols
            assert len(rows) == 5
            
            # Verify prior_close is populated, current_price is NULL
            for row in rows:
                assert row[1] is None, f"Current price should be NULL for {row[0]}"
                assert row[2] is not None, f"Prior close is NULL for {row[0]}"
    
    def test_time_window_rejection(self, futures_processor):
        """Test that files outside time windows are rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create 3pm file (should be rejected)
            filepath = Path(temp_dir) / 'Futures_20250715_1500.csv'
            self.create_futures_csv(filepath, filepath.name)
            
            # Process file
            result = futures_processor.process_file(filepath)
            assert result is None, f"Expected None for 3pm file but got {result}"
    
    def test_edge_time_windows(self, futures_processor):
        """Test edge cases of time windows (±15 minutes)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_cases = [
                ('Futures_20250715_1345.csv', 'current_price'),  # 1:45pm - OK
                ('Futures_20250715_1344.csv', None),             # 1:44pm - Too early
                ('Futures_20250715_1431.csv', None),             # 2:31pm - Too late
                ('Futures_20250715_1545.csv', 'prior_close'),    # 3:45pm - OK
                ('Futures_20250715_1631.csv', None),             # 4:31pm - Too late
            ]
            
            for filename, expected in test_cases:
                filepath = Path(temp_dir) / filename
                self.create_futures_csv(filepath, filename)
                result = futures_processor.process_file(filepath)
                assert result == expected, f"File {filename}: expected {expected} but got {result}"
    
    def test_duplicate_processing_prevention(self, futures_processor, storage):
        """Test that files are not processed twice."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
            self.create_futures_csv(filepath, filepath.name)
            
            # Process file first time
            result1 = futures_processor.process_file(filepath)
            assert result1 == 'current_price'
            
            # Get initial row count
            data1 = storage.get_futures_prices(date(2025, 7, 15))
            initial_count = len(data1)
            
            # Process same file again
            result2 = futures_processor.process_file(filepath)
            assert result2 == 'already_processed'
            
            # Verify no duplicate rows
            data2 = storage.get_futures_prices(date(2025, 7, 15))
            assert len(data2) == initial_count
    
    def test_update_vs_insert_logic(self, futures_processor, storage):
        """Test that 2pm updates existing rows and 4pm inserts new rows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First, process 4pm file from previous day
            filepath1 = Path(temp_dir) / 'Futures_20250714_1600.csv'
            self.create_futures_csv(filepath1, filepath1.name, px_settle=109.5)
            result1 = futures_processor.process_file(filepath1)
            assert result1 == 'prior_close'
            
            # Verify prior close for July 15
            df1 = storage.get_futures_by_date(date(2025, 7, 15))
            assert len(df1) == 5
            assert df1.iloc[0]['prior_close'] == 109.5
            assert pd.isna(df1.iloc[0]['current_price'])
            
            # Now process 2pm file for July 15
            filepath2 = Path(temp_dir) / 'Futures_20250715_1400.csv'
            self.create_futures_csv(filepath2, filepath2.name, px_last=110.25)
            result2 = futures_processor.process_file(filepath2)
            assert result2 == 'current_price'
            
            # Verify UPDATE occurred (not insert)
            df2 = storage.get_futures_by_date(date(2025, 7, 15))
            assert len(df2) == 5  # Same number of rows
            assert df2.iloc[0]['prior_close'] == 109.5  # Prior close unchanged
            assert df2.iloc[0]['current_price'] == 110.25  # Current price updated
    
    def test_options_processing_with_metadata(self, options_processor, storage):
        """Test options processing includes expire_dt and moneyness."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'Options_20250715_1400.csv'
            self.create_options_csv(filepath, filepath.name)
            
            # Process file
            result = options_processor.process_file(filepath)
            assert result == 'current_price'
            
            # Verify data
            df = storage.get_options_by_date(date(2025, 7, 15))
            assert len(df) == 4
            
            # Check metadata fields
            for _, row in df.iterrows():
                assert pd.notna(row['expire_dt'])
                assert row['moneyness'] in ['ATM', 'OTM']
    
    def test_concurrent_file_processing(self, storage):
        """Test processing multiple files concurrently."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple processors with shared storage
            processors = [FuturesProcessor(storage) for _ in range(3)]
            
            # Create test files
            files = []
            for i in range(3):
                filepath = Path(temp_dir) / f'Futures_2025071{5+i}_1400.csv'
                self.create_futures_csv(filepath, filepath.name)
                files.append(filepath)
            
            # Process files concurrently
            results = [None] * 3
            def process_file(idx):
                results[idx] = processors[idx].process_file(files[idx])
            
            threads = []
            for i in range(3):
                t = threading.Thread(target=process_file, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            # Verify all succeeded
            assert all(r == 'current_price' for r in results)
            
            # Verify data integrity
            for i in range(3):
                df = storage.get_futures_by_date(date(2025, 7, 15 + i))
                assert len(df) == 5  # Each file has 5 symbols
    
    def test_malformed_csv_handling(self, futures_processor):
        """Test handling of malformed CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Missing required column
            filepath1 = Path(temp_dir) / 'Futures_20250715_1400.csv'
            df1 = pd.DataFrame({'SYMBOL': ['TU'], 'PX_LAST': [110.5]})  # Missing PX_SETTLE
            df1.to_csv(filepath1, index=False)
            
            result1 = futures_processor.process_file(filepath1)
            assert result1 is None
            
            # Empty file
            filepath2 = Path(temp_dir) / 'Futures_20250715_1401.csv'
            open(filepath2, 'w').close()
            
            result2 = futures_processor.process_file(filepath2)
            assert result2 is None
            
            # Non-numeric prices
            filepath3 = Path(temp_dir) / 'Futures_20250715_1402.csv'
            df3 = pd.DataFrame({
                'SYMBOL': ['TU'],
                'PX_LAST': ['invalid'],
                'PX_SETTLE': [110.5]
            })
            df3.to_csv(filepath3, index=False)
            
            result3 = futures_processor.process_file(filepath3)
            assert result3 == 'current_price'  # Should process valid rows 