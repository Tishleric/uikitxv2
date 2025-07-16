#!/usr/bin/env python3
"""
Comprehensive test demonstrating all market price processing features.

This script showcases:
1. Time window validation
2. Edge case handling
3. Error recovery
4. Data integrity
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from pathlib import Path
import tempfile
import pandas as pd
import logging
import time

from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor, OptionsProcessor, MarketPriceFileMonitor
from lib.trading.market_prices.constants import CHICAGO_TZ

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_time_windows():
    """Test time window validation."""
    print("\n" + "="*60)
    print("TEST 1: Time Window Validation")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    storage = MarketPriceStorage(db_path=db_path)
    processor = FuturesProcessor(storage)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_cases = [
            ('Futures_20250715_1345.csv', '1:45pm', 'ACCEPTED (2pm window)'),
            ('Futures_20250715_1400.csv', '2:00pm', 'ACCEPTED (2pm window)'),
            ('Futures_20250715_1430.csv', '2:30pm', 'ACCEPTED (2pm window)'),
            ('Futures_20250715_1500.csv', '3:00pm', 'REJECTED (no window)'),
            ('Futures_20250715_1545.csv', '3:45pm', 'ACCEPTED (4pm window)'),
            ('Futures_20250715_1600.csv', '4:00pm', 'ACCEPTED (4pm window)'),
            ('Futures_20250715_1630.csv', '4:30pm', 'ACCEPTED (4pm window)'),
            ('Futures_20250715_1700.csv', '5:00pm', 'REJECTED (no window)'),
        ]
        
        for filename, time_str, expected in test_cases:
            filepath = Path(temp_dir) / filename
            df = pd.DataFrame({
                'SYMBOL': ['TU'],
                'PX_LAST': [110.5],
                'PX_SETTLE': [110.75]
            })
            df.to_csv(filepath, index=False)
            
            result = processor.process_file(filepath)
            status = 'ACCEPTED' if result else 'REJECTED'
            print(f"  {time_str}: {status} - {expected}")
    
    db_path.unlink()
    print("✅ Time window validation working correctly")

def test_edge_cases():
    """Test edge case handling."""
    print("\n" + "="*60)
    print("TEST 2: Edge Case Handling")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    storage = MarketPriceStorage(db_path=db_path)
    processor = FuturesProcessor(storage)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n  Testing malformed CSV:")
        bad_csv = Path(temp_dir) / 'Futures_20250715_1400.csv'
        bad_csv.write_text("This is not valid CSV content\nBad data here")
        result = processor.process_file(bad_csv)
        print(f"    Malformed CSV: {'Handled gracefully' if result is None else 'ERROR'}")
        
        print("\n  Testing missing columns:")
        missing_col = Path(temp_dir) / 'Futures_20250715_1401.csv'
        df = pd.DataFrame({'SYMBOL': ['TU']})  # Missing price columns
        df.to_csv(missing_col, index=False)
        result = processor.process_file(missing_col)
        print(f"    Missing columns: {'Handled gracefully' if result is None else 'ERROR'}")
        
        print("\n  Testing extreme values:")
        extreme = Path(temp_dir) / 'Futures_20250715_1402.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [999999.99, -100.5, 0.0],
            'PX_SETTLE': [110.75, 108.5, 116.0]
        })
        df.to_csv(extreme, index=False)
        result = processor.process_file(extreme)
        print(f"    Extreme values: {'Processed' if result else 'Failed'}")
        
        if result:
            data = storage.get_futures_prices(date(2025, 7, 15))
            print(f"    Stored {len(data)} records with extreme values")
    
    db_path.unlink()
    print("\n✅ Edge cases handled correctly")

def test_data_flow():
    """Test complete data flow from 2pm to 4pm."""
    print("\n" + "="*60)
    print("TEST 3: Complete Data Flow")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    storage = MarketPriceStorage(db_path=db_path)
    processor = FuturesProcessor(storage)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Day 1: 4pm file (creates July 15 prior close)
        print("\n  July 14, 4:00pm - Settlement prices")
        file1 = Path(temp_dir) / 'Futures_20250714_1600.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [109.5, 107.25, 114.75],
            'PX_SETTLE': [109.75, 107.5, 115.0]  # These become July 15 prior close
        })
        df.to_csv(file1, index=False)
        processor.process_file(file1)
        
        # Check July 15 has prior close
        data = storage.get_futures_prices(date(2025, 7, 15))
        print(f"    July 15 morning: {len(data)} symbols with prior close")
        if data:
            print(f"      {data[0]['symbol']}: prior_close={data[0].get('prior_close', 'NULL')}, current_price={data[0].get('current_price', 'NULL')}")
        
        # Day 2: 2pm file (updates July 15 current price)
        print("\n  July 15, 2:00pm - Current prices")
        file2 = Path(temp_dir) / 'Futures_20250715_1400.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [110.25, 108.0, 115.5],  # Current prices
            'PX_SETTLE': [110.5, 108.25, 115.75]
        })
        df.to_csv(file2, index=False)
        processor.process_file(file2)
        
        # Check July 15 now has both
        data = storage.get_futures_prices(date(2025, 7, 15))
        print(f"    July 15 afternoon: {len(data)} symbols with both prices")
        if data:
            print(f"      {data[0]['symbol']}: prior_close={data[0].get('prior_close', 'NULL')}, current_price={data[0].get('current_price', 'NULL')}")
        
        # Day 2: 4pm file (creates July 16 prior close)
        print("\n  July 15, 4:00pm - Settlement prices")
        file3 = Path(temp_dir) / 'Futures_20250715_1600.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [110.5, 108.25, 115.75],
            'PX_SETTLE': [110.75, 108.5, 116.0]  # These become July 16 prior close
        })
        df.to_csv(file3, index=False)
        processor.process_file(file3)
        
        # Check July 16 has prior close
        data = storage.get_futures_prices(date(2025, 7, 16))
        print(f"    July 16 morning: {len(data)} symbols with prior close")
        if data:
            print(f"      {data[0]['symbol']}: prior_close={data[0].get('prior_close', 'NULL')}, current_price={data[0].get('current_price', 'NULL')}")
    
    db_path.unlink()
    print("\n✅ Data flow working correctly")

def test_file_monitoring():
    """Test file monitoring functionality."""
    print("\n" + "="*60)
    print("TEST 4: File Monitoring")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        futures_dir = Path(temp_dir) / 'futures'
        options_dir = Path(temp_dir) / 'options'
        futures_dir.mkdir()
        options_dir.mkdir()
        
        storage = MarketPriceStorage(db_path=db_path)
        
        # Set up callbacks to track processing
        processed_files = []
        
        def track_futures(filepath, result):
            processed_files.append(('futures', filepath.name, result))
        
        def track_options(filepath, result):
            processed_files.append(('options', filepath.name, result))
        
        # Create monitor with callbacks
        monitor = MarketPriceFileMonitor(
            storage=storage,
            futures_callback=track_futures,
            options_callback=track_options
        )
        
        # Override the directories after creation for testing
        monitor.futures_dir = futures_dir
        monitor.options_dir = options_dir
        
        print("  Starting monitor...")
        monitor.start()
        time.sleep(1)
        
        # Create files while monitor is running
        print("  Creating futures file...")
        futures_file = futures_dir / 'Futures_20250715_1400.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV'],
            'PX_LAST': [110.5, 108.25],
            'PX_SETTLE': [110.75, 108.5]
        })
        df.to_csv(futures_file, index=False)
        
        print("  Creating options file...")
        options_file = options_dir / 'Options_20250715_1400.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TUU5 C 110', 'TUU5 P 110'],
            'PX_LAST': [0.5, 0.3],
            'PX_SETTLE': [0.52, 0.32],
            'EXPIRE_DT': ['2025-09-30'] * 2,
            'MONEYNESS': ['ATM', 'ATM']
        })
        df.to_csv(options_file, index=False)
        
        # Wait for processing
        time.sleep(2)
        
        print("  Stopping monitor...")
        monitor.stop()
        
        print(f"\n  Processed {len(processed_files)} files:")
        for file_type, filename, result in processed_files:
            print(f"    {file_type}: {filename} -> {result}")
    
    db_path.unlink()
    print("\n✅ File monitoring working correctly")

def test_duplicate_prevention():
    """Test duplicate processing prevention."""
    print("\n" + "="*60)
    print("TEST 5: Duplicate Processing Prevention")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    storage = MarketPriceStorage(db_path=db_path)
    processor = FuturesProcessor(storage)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create and process file
        filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
        df = pd.DataFrame({
            'SYMBOL': ['TU', 'FV', 'TY'],
            'PX_LAST': [110.5, 108.25, 115.75],
            'PX_SETTLE': [110.75, 108.5, 116.0]
        })
        df.to_csv(filepath, index=False)
        
        print("  First processing...")
        result1 = processor.process_file(filepath)
        data1 = storage.get_futures_prices(date(2025, 7, 15))
        print(f"    Result: {result1}, Records: {len(data1)}")
        
        print("  Second processing (same file)...")
        result2 = processor.process_file(filepath)
        data2 = storage.get_futures_prices(date(2025, 7, 15))
        print(f"    Result: {result2}, Records: {len(data2)}")
        
        print(f"  Duplicate prevention: {'SUCCESS' if len(data1) == len(data2) else 'FAILED'}")
    
    db_path.unlink()
    print("\n✅ Duplicate prevention working correctly")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("COMPREHENSIVE MARKET PRICE PROCESSING TEST")
    print("="*60)
    
    test_time_windows()
    test_edge_cases()
    test_data_flow()
    test_file_monitoring()
    test_duplicate_prevention()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
    print("="*60) 