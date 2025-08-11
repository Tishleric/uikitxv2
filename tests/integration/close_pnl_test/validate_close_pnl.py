"""
End-to-End Validation for Close PnL Implementation
Confirms the exact behavior before implementing in production
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from test_data_setup import create_test_database, insert_test_data
from test_positions_aggregator import TestPositionsAggregator
from test_update_callback import test_update_positions_table, test_close_price_availability


def validate_calculations(db_path, expected_values):
    """Validate that calculated values match expectations"""
    
    conn = sqlite3.connect(db_path)
    
    # Query the final positions table
    query = """
    SELECT 
        symbol,
        open_position,
        fifo_realized_pnl,
        fifo_unrealized_pnl,
        fifo_unrealized_pnl_close,
        (fifo_realized_pnl + fifo_unrealized_pnl) as pnl_live,
        (fifo_realized_pnl + fifo_unrealized_pnl_close) as pnl_close
    FROM positions
    ORDER BY symbol
    """
    
    results_df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    
    all_passed = True
    
    for _, row in results_df.iterrows():
        symbol = row['symbol']
        if symbol not in expected_values:
            continue
            
        expected = expected_values[symbol]
        print(f"\n{symbol}:")
        print("-" * 40)
        
        # Validate Live PnL
        actual_live = row['pnl_live']
        expected_live = expected['expected_pnl_live']
        live_match = abs(actual_live - expected_live) < 0.01
        
        print(f"  Live PnL:")
        print(f"    Expected: ${expected_live:,.2f}")
        print(f"    Actual:   ${actual_live:,.2f}")
        print(f"    Status:   {'✓ PASS' if live_match else '✗ FAIL'}")
        
        if not live_match:
            all_passed = False
            print(f"    Details: Realized={row['fifo_realized_pnl']}, Unrealized={row['fifo_unrealized_pnl']}")
        
        # Validate Close PnL
        actual_close = row['pnl_close']
        expected_close = expected['expected_pnl_close']
        
        if expected_close is None:
            # Should be NULL/NaN
            close_match = pd.isna(actual_close)
            print(f"  Close PnL:")
            print(f"    Expected: NULL (no today's close)")
            print(f"    Actual:   {'NULL' if pd.isna(actual_close) else f'${actual_close:,.2f}'}")
            print(f"    Status:   {'✓ PASS' if close_match else '✗ FAIL'}")
        else:
            close_match = abs(actual_close - expected_close) < 0.01
            print(f"  Close PnL:")
            print(f"    Expected: ${expected_close:,.2f}")
            print(f"    Actual:   ${actual_close:,.2f}")
            print(f"    Status:   {'✓ PASS' if close_match else '✗ FAIL'}")
            
            if not close_match:
                print(f"    Details: Realized={row['fifo_realized_pnl']}, Unrealized Close={row['fifo_unrealized_pnl_close']}")
        
        if not close_match:
            all_passed = False
    
    print("\n" + "="*80)
    print(f"OVERALL VALIDATION: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("="*80)
    
    return all_passed


def run_full_validation():
    """Run complete validation suite"""
    
    print("CLOSE PNL IMPLEMENTATION VALIDATION")
    print("="*80)
    
    # Step 1: Create test database
    print("\n1. Creating test database...")
    db_path = 'test_close_pnl.db'
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = create_test_database(db_path)
    expected_values = insert_test_data(conn)
    conn.close()
    print("   ✓ Test database created with sample data")
    
    # Step 2: Run positions aggregator
    print("\n2. Running positions aggregator...")
    aggregator = TestPositionsAggregator(db_path)
    positions = aggregator.load_and_calculate_positions()
    print("   ✓ Positions calculated successfully")
    
    # Step 3: Test close price availability logic
    print("\n3. Testing close price availability...")
    test_close_price_availability(db_path)
    
    # Step 4: Test the update callback
    print("\n4. Testing FRGMonitor callback logic...")
    callback_results = test_update_positions_table(db_path)
    
    # Step 5: Validate calculations
    print("\n5. Validating calculations...")
    validation_passed = validate_calculations(db_path, expected_values)
    
    # Step 6: Summary of code changes needed
    print("\n" + "="*80)
    print("EXACT CODE CHANGES REQUIRED")
    print("="*80)
    
    print("\n1. Database Schema Changes:")
    print("   - ALTER TABLE positions ADD COLUMN fifo_unrealized_pnl_close REAL DEFAULT 0;")
    print("   - ALTER TABLE positions ADD COLUMN lifo_unrealized_pnl_close REAL DEFAULT 0;")
    
    print("\n2. PositionsAggregator Changes (lib/trading/pnl_fifo_lifo/positions_aggregator.py):")
    print("   - In _load_positions_from_db(): Calculate close unrealized PnL alongside live")
    print("   - In _update_positions_with_greeks(): Include close PnL columns")
    print("   - In _write_positions_to_db(): Write close PnL values to new columns")
    
    print("\n3. FRGMonitor Callback Changes (apps/dashboards/main/app.py):")
    print("   - Remove time-based conditional (lines 3428-3456)")
    print("   - Add date-based check on close price timestamp")
    print("   - Change pnl_close calculation to use fifo_unrealized_pnl_close")
    
    print("\n4. Key Implementation Details:")
    print("   - Close PnL = fifo_realized_pnl + fifo_unrealized_pnl_close")
    print("   - Show close PnL only when close price timestamp is today's date")
    print("   - Use same calculate_unrealized_pnl() function with 'close' prices")
    print("   - No changes to daily_positions table")
    
    return validation_passed


if __name__ == "__main__":
    # Run the full validation
    passed = run_full_validation()
    
    # Clean up test database
    if os.path.exists('test_close_pnl.db'):
        os.remove('test_close_pnl.db')
        print("\n✓ Test database cleaned up")
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)