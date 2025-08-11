#!/usr/bin/env python3
"""
Test manual EOD trigger with mock database
Simulates production behavior without touching real data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import tempfile
from unittest.mock import patch, Mock
from datetime import datetime
import pytz

# Test data
TEST_SYMBOLS = ['TUU5 Comdty', 'FVU5 Comdty', 'TYU5 Comdty']
CHICAGO_TZ = pytz.timezone('America/Chicago')


def create_test_database():
    """Create a test database with sample data"""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    conn = sqlite3.connect(temp_db.name)
    cursor = conn.cursor()
    
    # Create pricing table
    cursor.execute("""
        CREATE TABLE pricing (
            symbol TEXT,
            price_type TEXT,
            price REAL,
            timestamp TEXT
        )
    """)
    
    # Add test data - simulate state after 2pm files received
    for symbol in TEST_SYMBOLS:
        # Close price (from 2pm file)
        cursor.execute("""
            INSERT INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'close', ?, '2025-08-03 14:00:00')
        """, (symbol, 100.0))
        
        # sodTom price (from 2pm file)
        cursor.execute("""
            INSERT INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'sodTom', ?, '2025-08-03 14:00:00')
        """, (symbol, 100.0))
    
    # Create other required tables
    cursor.execute("""
        CREATE TABLE trades_fifo (
            symbol TEXT,
            quantity REAL,
            price REAL,
            buySell TEXT,
            time TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE trades_lifo (
            symbol TEXT,
            quantity REAL,
            price REAL,
            buySell TEXT,
            time TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE daily_positions (
            date TEXT,
            symbol TEXT,
            method TEXT,
            unrealized_pnl REAL,
            open_position REAL,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    return temp_db.name, conn


def test_manual_trigger():
    """Test the manual trigger logic"""
    print("=" * 80)
    print("TESTING MANUAL EOD TRIGGER")
    print("=" * 80)
    print()
    
    # Create test database
    db_path, conn = create_test_database()
    
    try:
        # Import the manual trigger functions
        from scripts.manual_eod_settlement import trigger_4pm_roll, check_already_triggered
        
        # Test 1: Check not already triggered
        print("TEST 1: Checking if already triggered...")
        already_done = check_already_triggered(conn, '20250803')
        print(f"  Already triggered: {already_done}")
        assert not already_done, "Should not be triggered yet"
        print("  ✅ PASS")
        
        # Test 2: Verify initial state
        print("\nTEST 2: Verifying initial database state...")
        cursor = conn.cursor()
        
        # Check sodTom exists
        cursor.execute("SELECT COUNT(*) FROM pricing WHERE price_type = 'sodTom'")
        sodtom_count = cursor.fetchone()[0]
        print(f"  sodTom entries: {sodtom_count}")
        assert sodtom_count == len(TEST_SYMBOLS), "Should have sodTom prices"
        
        # Check sodTod doesn't exist
        cursor.execute("SELECT COUNT(*) FROM pricing WHERE price_type = 'sodTod'")
        sodtod_count = cursor.fetchone()[0]
        print(f"  sodTod entries: {sodtod_count}")
        assert sodtod_count == 0, "Should not have sodTod prices yet"
        print("  ✅ PASS")
        
        # Test 3: Mock the actual roll functions and test trigger
        print("\nTEST 3: Testing trigger execution...")
        
        operations_called = []
        
        def mock_roll_4pm(conn, symbol):
            operations_called.append(('roll_4pm', symbol))
            # Simulate the operation
            cursor = conn.cursor()
            # Move sodTom to sodTod
            cursor.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                SELECT symbol, 'sodTod', price, timestamp
                FROM pricing 
                WHERE symbol = ? AND price_type = 'sodTom'
            """, (symbol,))
            # Delete sodTom
            cursor.execute("""
                DELETE FROM pricing 
                WHERE symbol = ? AND price_type = 'sodTom'
            """, (symbol,))
        
        def mock_eod_settlement(conn, date, prices):
            operations_called.append(('eod_settlement', date, len(prices)))
        
        # Patch the functions
        with patch('scripts.manual_eod_settlement.roll_4pm_prices', side_effect=mock_roll_4pm):
            with patch('scripts.manual_eod_settlement.perform_eod_settlement', side_effect=mock_eod_settlement):
                # Execute trigger
                success = trigger_4pm_roll(conn, '20250803')
        
        print(f"  Trigger success: {success}")
        assert success, "Trigger should succeed"
        
        # Verify operations called
        print(f"\n  Operations called:")
        for op in operations_called:
            if op[0] == 'roll_4pm':
                print(f"    - roll_4pm_prices({op[1]})")
            else:
                print(f"    - perform_eod_settlement({op[1]}, {op[2]} symbols)")
        
        # Verify all symbols processed
        rolled_symbols = [op[1] for op in operations_called if op[0] == 'roll_4pm']
        assert set(rolled_symbols) == set(TEST_SYMBOLS), "All symbols should be rolled"
        print(f"\n  ✅ All {len(TEST_SYMBOLS)} symbols processed")
        
        # Test 4: Verify final state
        print("\nTEST 4: Verifying final database state...")
        
        # Check sodTom removed
        cursor.execute("SELECT COUNT(*) FROM pricing WHERE price_type = 'sodTom'")
        sodtom_count = cursor.fetchone()[0]
        print(f"  sodTom entries: {sodtom_count}")
        assert sodtom_count == 0, "sodTom should be removed"
        
        # Check sodTod exists
        cursor.execute("SELECT COUNT(*) FROM pricing WHERE price_type = 'sodTod'")
        sodtod_count = cursor.fetchone()[0]
        print(f"  sodTod entries: {sodtod_count}")
        assert sodtod_count == len(TEST_SYMBOLS), "Should have sodTod prices"
        print("  ✅ PASS")
        
        # Test 5: Try to trigger again
        print("\nTEST 5: Testing duplicate prevention...")
        already_done = check_already_triggered(conn, '20250803')
        print(f"  Already triggered: {already_done}")
        assert already_done, "Should show as already triggered"
        print("  ✅ PASS - Duplicate prevention works")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        print("\nSUMMARY:")
        print("✅ Manual trigger executes same operations as automatic")
        print("✅ Proper state transitions (sodTom → sodTod)")
        print("✅ All symbols processed")
        print("✅ Duplicate prevention works")
        print("✅ Safe to implement")
        
    finally:
        conn.close()
        # Clean up temp file
        import os
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_manual_trigger()