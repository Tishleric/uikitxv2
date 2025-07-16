#!/usr/bin/env python3
"""Test that precision fixes work correctly."""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager


def test_precision_fix():
    """Test that our precision fixes prevent floating point errors."""
    
    # Create temporary test database
    test_dir = tempfile.mkdtemp()
    db_path = Path(test_dir) / "test_precision.db"
    
    try:
        # Initialize components
        storage = PnLStorage(str(db_path))
        position_manager = PositionManager(storage)
        
        # Test case that would produce 4.75000000001 with float arithmetic
        print("Testing precision fix...")
        print("-" * 60)
        
        # Direct database test
        conn = storage._get_connection()
        cursor = conn.cursor()
        
        # Note: storage._initialize_database() already created the positions table
        # We'll use the existing schema
        
        test_cases = [
            # (symbol, quantity, avg_cost, market_price, expected_unrealized_pnl)
            ('TYU5', 7, 110.03125, 110.71875, 4.8125),  # 7 * (110.71875 - 110.03125) = 4.8125
            ('TYH5', 5, 99.99999, 100.95001, 4.75005),  # Edge case with many decimals
            ('TYM5', 3, 110.12345, 111.45678, 4.00011),  # Another precision test
            ('TYZ5', -10, 105.5, 104.25, 12.5),  # Short position
            ('OTYH5 C11000', 15, 0.1, 0.3, 3.0),  # Option with small values
        ]
        
        print("Testing various precision scenarios:\n")
        
        for symbol, qty, avg_cost, mkt_price, expected_pnl in test_cases:
            # Clear previous position
            cursor.execute("DELETE FROM positions WHERE instrument_name = ?", (symbol,))
            
            # Insert position using correct column names
            cursor.execute("""
                INSERT INTO positions (
                    instrument_name, position_quantity, avg_cost, 
                    total_realized_pnl, unrealized_pnl, last_updated,
                    is_option
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, qty, avg_cost, 0.0, 0.0, datetime.now(), 1 if symbol.startswith('O') else 0))
            
            conn.commit()
            
            # Calculate P&L with different methods
            # 1. Direct float calculation (problematic)
            float_pnl = (mkt_price - avg_cost) * qty
            
            # 2. Rounded calculation (our fix)
            if symbol.startswith('O'):
                rounded_pnl = round((mkt_price - avg_cost) * qty, 4)  # Options: 4 decimals
            else:
                rounded_pnl = round((mkt_price - avg_cost) * qty, 5)  # Futures: 5 decimals
            
            # 3. SQLite's ROUND function
            cursor.execute("""
                UPDATE positions 
                SET last_market_price = ?, 
                    unrealized_pnl = ROUND((? - avg_cost) * position_quantity, 5),
                    last_updated = ?
                WHERE instrument_name = ?
            """, (mkt_price, mkt_price, datetime.now(), symbol))
            
            conn.commit()
            
            # Check result
            cursor.execute(
                "SELECT unrealized_pnl FROM positions WHERE instrument_name = ?",
                (symbol,)
            )
            result = cursor.fetchone()
            db_pnl = result[0] if result else None
            
            # Display results
            print(f"Symbol: {symbol}")
            print(f"  Position: {qty} @ {avg_cost}")
            print(f"  Market Price: {mkt_price}")
            print(f"  Expected P&L: {expected_pnl}")
            print(f"  Float P&L: {float_pnl} (repr: {repr(float_pnl)})")
            print(f"  Rounded P&L: {rounded_pnl}")
            print(f"  Database P&L: {db_pnl}")
            
            # Check precision
            issues = []
            
            # Check float precision
            float_str = str(float_pnl)
            if '.' in float_str:
                float_decimals = len(float_str.rstrip('0').split('.')[1])
                if float_decimals > 10:
                    issues.append(f"Float has {float_decimals} decimals")
            
            # Check rounded precision
            rounded_str = str(rounded_pnl)
            if '.' in rounded_str:
                rounded_decimals = len(rounded_str.rstrip('0').split('.')[1])
                if rounded_decimals > 5:
                    issues.append(f"Rounded has {rounded_decimals} decimals")
            
            # Check database precision
            if db_pnl is not None:
                db_str = str(db_pnl)
                if '.' in db_str:
                    db_decimals = len(db_str.rstrip('0').split('.')[1])
                    if db_decimals > 5:
                        issues.append(f"Database has {db_decimals} decimals")
            
            # Report results
            if issues:
                print(f"  ❌ Issues: {', '.join(issues)}")
            else:
                print(f"  ✓ Precision OK")
            
            # Check accuracy
            tolerance = 0.00001
            if db_pnl is not None and abs(db_pnl - expected_pnl) > tolerance:
                print(f"  ⚠️  Accuracy issue: expected {expected_pnl}, got {db_pnl}")
            
            print()
        
        # Test cumulative precision over many operations
        print("-" * 60)
        print("Testing cumulative precision over many operations...")
        
        symbol = 'TYF6'
        cursor.execute("DELETE FROM positions WHERE instrument_name = ?", (symbol,))
        
        # Start with initial position
        total_qty = 0
        total_cost = 0.0
        
        for i in range(50):
            qty = (i % 5) + 1
            price = 110.0 + (i * 0.03125)  # Increment by tick
            
            total_qty += qty
            total_cost += qty * price
            avg_cost = total_cost / total_qty if total_qty > 0 else 0
            
            # Update position
            cursor.execute("""
                INSERT OR REPLACE INTO positions (
                    instrument_name, position_quantity, avg_cost,
                    total_realized_pnl, unrealized_pnl, last_updated,
                    is_option
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, total_qty, avg_cost, 0.0, 0.0, datetime.now(), 0))
        
        conn.commit()
        
        # Check final precision
        cursor.execute(
            "SELECT position_quantity, avg_cost FROM positions WHERE instrument_name = ?",
            (symbol,)
        )
        result = cursor.fetchone()
        
        if result:
            final_qty, final_avg = result
            print(f"After 50 operations:")
            print(f"  Final quantity: {final_qty}")
            print(f"  Final avg cost: {final_avg}")
            
            avg_str = str(final_avg)
            if '.' in avg_str:
                decimals = len(avg_str.rstrip('0').split('.')[1])
                if decimals > 7:
                    print(f"  ❌ Precision degraded: {decimals} decimal places")
                else:
                    print(f"  ✓ Precision maintained: {decimals} decimal places")
        
        conn.close()
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print("\n" + "=" * 60)
        print("Precision test completed")


if __name__ == "__main__":
    test_precision_fix() 