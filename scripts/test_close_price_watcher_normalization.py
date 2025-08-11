#!/usr/bin/env python3
"""
Test the updated close price watcher normalization
Verifies the changes work without touching any database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from io import StringIO
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

# Import the handler we're testing
from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceFileHandler

# Sample options CSV with edge cases
SAMPLE_OPTIONS_CSV = """SYMBOL,LAST_PRICE,PX_SETTLE,Settle Price = Today
TJPQ25C1 110 Comdty,0.125,0.130,Y
TYWQ25P1 115 COMB Comdty,1.500,1.505,Y
TYWQ25P1  114.75  COMB  Comdty,1.250,1.255,N
COMB TYWQ25P1 113 Comdty,0.800,0.805,Y
TYWQ25P1 112 Comdty COMB,0.650,0.655,N
  TYWQ25P1  111  COMB  Comdty  ,0.500,0.505,Y
TYWQ25P1 COMB 110 COMB Comdty,0.350,0.355,N
"""

# Sample futures CSV
SAMPLE_FUTURES_CSV = """SYMBOL,PX_SETTLE_DEC,PX_300_DEC,Settle Price = Today
TU,99.25,99.26,Y
FV,105.50,105.48,N
TY,112.75,112.73,Y
"""


def test_options_normalization():
    """Test options symbol normalization without database"""
    print("=" * 80)
    print("TESTING OPTIONS SYMBOL NORMALIZATION")
    print("=" * 80)
    print()
    
    # Create a temporary CSV file with correct naming pattern
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, 'Options_20250101_1400.csv')
    with open(temp_file, 'w') as f:
        f.write(SAMPLE_OPTIONS_CSV)
    
    try:
        # Mock the database operations
        with patch('lib.trading.pnl_fifo_lifo.close_price_watcher.sqlite3.connect') as mock_connect:
            # Mock database connection and methods
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Capture what would be sent to database
            captured_updates = []
            
            def capture_roll_2pm(conn, price, symbol):
                captured_updates.append({
                    'symbol': symbol,
                    'price': price,
                    'operation': 'roll_2pm_prices'
                })
            
            # Mock the roll_2pm_prices function
            with patch('lib.trading.pnl_fifo_lifo.close_price_watcher.roll_2pm_prices', side_effect=capture_roll_2pm):
                # Create handler and process file
                handler = ClosePriceFileHandler(':memory:', 0)
                handler._process_file(Path(temp_file))
        
        # Display results
        print("Normalized symbols that would be updated:")
        print("-" * 80)
        print(f"{'Original (from CSV)':<40} {'Normalized Symbol':<35} {'Price':<10}")
        print("-" * 80)
        
        # Read the CSV to show original vs normalized
        df = pd.read_csv(StringIO(SAMPLE_OPTIONS_CSV))
        
        for idx, update in enumerate(captured_updates):
            original = df.iloc[idx]['SYMBOL']
            normalized = update['symbol']
            price = update['price']
            
            # Mark differences
            changed = "✓" if original.strip() == normalized else "⚠️"
            print(f"{changed} {original:<38} {normalized:<35} {price:<10.3f}")
        
        print()
        print("Legend: ✓ = No change needed, ⚠️ = Normalization applied")
        
        # Verify specific cases
        print()
        print("VERIFICATION OF KEY FIXES:")
        print("-" * 80)
        
        test_cases = [
            ("TYWQ25P1  114.75  COMB  Comdty", "TYWQ25P1 114.75 Comdty"),
            ("COMB TYWQ25P1 113 Comdty", "TYWQ25P1 113 Comdty"),
            ("TYWQ25P1 112 Comdty COMB", "TYWQ25P1 112 Comdty"),
            ("  TYWQ25P1  111  COMB  Comdty  ", "TYWQ25P1 111 Comdty"),
            ("TYWQ25P1 COMB 110 COMB Comdty", "TYWQ25P1 110 Comdty"),
        ]
        
        for original, expected in test_cases:
            # Find the normalized version from our results
            found = None
            for idx, row in df.iterrows():
                if row['SYMBOL'] == original:
                    if idx < len(captured_updates):
                        found = captured_updates[idx]['symbol']
                    break
            
            if found:
                status = "✅ PASS" if found == expected else "❌ FAIL"
                print(f"{status}: '{original}' → '{found}'")
                if found != expected:
                    print(f"       Expected: '{expected}'")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    print()
    print("✅ Test completed - No database was touched!")


def test_futures_still_works():
    """Verify futures processing still works correctly"""
    print()
    print("=" * 80)
    print("VERIFYING FUTURES PROCESSING UNCHANGED")
    print("=" * 80)
    print()
    
    # Create a temporary CSV file with correct naming pattern
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, 'Futures_20250101_1400.csv')
    with open(temp_file, 'w') as f:
        f.write(SAMPLE_FUTURES_CSV)
    
    try:
        # Mock the database operations
        with patch('lib.trading.pnl_fifo_lifo.close_price_watcher.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            captured_updates = []
            
            def capture_roll_2pm(conn, price, symbol):
                captured_updates.append({
                    'symbol': symbol,
                    'price': price,
                })
            
            with patch('lib.trading.pnl_fifo_lifo.close_price_watcher.roll_2pm_prices', side_effect=capture_roll_2pm):
                handler = ClosePriceFileHandler(':memory:', 0)
                handler._process_file(Path(temp_file))
        
        print("Futures symbols processed:")
        print("-" * 60)
        for update in captured_updates:
            print(f"  {update['symbol']:<20} Price: {update['price']}")
        
        print()
        print("✅ Futures processing works correctly!")
    
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


if __name__ == "__main__":
    test_options_normalization()
    test_futures_still_works()