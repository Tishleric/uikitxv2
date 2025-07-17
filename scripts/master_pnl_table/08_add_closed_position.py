#!/usr/bin/env python3
"""
Add closed_position column to FULLPNL table.
First updates closed positions using ClosedPositionTracker, then populates from positions table.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from lib.trading.pnl_calculator.controller import PnLController

def add_closed_position_column():
    """Add closed_position column to FULLPNL table and populate from positions."""
    
    # Database path
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    if not pnl_db_path.exists():
        print(f"Error: P&L database not found at {pnl_db_path}")
        return
    
    # First, update closed positions using the controller
    print("Step 1: Updating closed positions using ClosedPositionTracker...")
    try:
        controller = PnLController()
        controller.update_closed_positions()
        print("✓ Closed positions updated successfully")
    except Exception as e:
        print(f"Error updating closed positions: {e}")
        print("Continuing anyway to add column...")
    
    # Now add the column to FULLPNL
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(FULLPNL)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'closed_position' not in columns:
            print("\nStep 2: Adding closed_position column to FULLPNL table...")
            cursor.execute("ALTER TABLE FULLPNL ADD COLUMN closed_position REAL")
            conn.commit()
            print("✓ closed_position column added")
        else:
            print("\nStep 2: closed_position column already exists")
        
        # Get all symbols from FULLPNL
        cursor.execute("SELECT symbol FROM FULLPNL")
        symbols = cursor.fetchall()
        print(f"\nStep 3: Processing {len(symbols)} symbols...")
        
        updated_count = 0
        missing_count = 0
        zero_closed_count = 0
        
        for (symbol,) in symbols:
            print(f"\nProcessing: {symbol}")
            
            # Query positions table for closed_quantity
            cursor.execute("""
                SELECT closed_quantity 
                FROM positions 
                WHERE instrument_name = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            
            if result:
                closed_qty = result[0]
                if closed_qty is not None:
                    cursor.execute("""
                        UPDATE FULLPNL 
                        SET closed_position = ?
                        WHERE symbol = ?
                    """, (closed_qty, symbol))
                    
                    if closed_qty == 0:
                        print(f"  Found closed quantity: {closed_qty} (no closures)")
                        zero_closed_count += 1
                    else:
                        print(f"  Found closed quantity: {closed_qty}")
                    updated_count += 1
                else:
                    print(f"  ⚠ Closed quantity is NULL in positions table")
                    missing_count += 1
            else:
                print(f"  ⚠ Symbol not found in positions table")
                missing_count += 1
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - closed_position Column Population:")
        print(f"{'='*60}")
        print(f"Total symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        print(f"  - With closures: {updated_count - zero_closed_count}")
        print(f"  - Without closures (0): {zero_closed_count}")
        print(f"Missing data: {missing_count} ({missing_count/len(symbols)*100:.1f}%)")
        
        # Show final table state
        print(f"\n{'='*60}")
        print("FULLPNL Table with closed_position:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, open_position, closed_position, px_last, px_settle
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'Open Pos':>10} {'Closed Pos':>10} {'px_last':>10} {'px_settle':>10}")
        print("-" * 80)
        
        # Print data
        for row in results:
            symbol, open_pos, closed_pos, px_last, px_settle = row
            open_str = f"{open_pos:.0f}" if open_pos is not None else "NULL"
            closed_str = f"{closed_pos:.0f}" if closed_pos is not None else "NULL"
            px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
            px_settle_str = f"{px_settle:.6f}" if px_settle is not None else "NULL"
            
            print(f"{symbol:<30} {open_str:>10} {closed_str:>10} {px_last_str:>10} {px_settle_str:>10}")
        
        # Check if there are any non-zero closed positions
        cursor.execute("""
            SELECT symbol, closed_position 
            FROM FULLPNL 
            WHERE closed_position IS NOT NULL AND closed_position != 0
        """)
        
        non_zero_closed = cursor.fetchall()
        if non_zero_closed:
            print(f"\n{'='*60}")
            print("Symbols with closed positions:")
            print(f"{'='*60}")
            for symbol, closed in non_zero_closed:
                print(f"  {symbol}: {closed:.0f} contracts closed")
        else:
            print(f"\n{'='*60}")
            print("No symbols have closed positions (all values are 0)")
            print("This may be normal if no positions were closed today")
            print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Adding closed_position column to FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    add_closed_position_column() 