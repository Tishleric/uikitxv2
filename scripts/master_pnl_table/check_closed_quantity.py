#!/usr/bin/env python3
"""Check closed_quantity column in positions table."""
import sqlite3
from pathlib import Path

def check_closed_quantity():
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    # Check table schema
    print("Positions table schema:")
    cursor.execute("PRAGMA table_info(positions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check if closed_quantity exists
    col_names = [col[1] for col in columns]
    if 'closed_quantity' in col_names:
        print("\n✓ closed_quantity column EXISTS")
        
        # Check data
        cursor.execute("""
            SELECT instrument_name, position_quantity, closed_quantity
            FROM positions
            ORDER BY instrument_name
        """)
        
        results = cursor.fetchall()
        print(f"\nPositions with closed_quantity data:")
        print(f"{'Symbol':<30} {'Open Position':>15} {'Closed Quantity':>15}")
        print("-" * 60)
        
        for inst, open_pos, closed_qty in results:
            open_str = f"{open_pos:.0f}" if open_pos is not None else "NULL"
            closed_str = f"{closed_qty:.0f}" if closed_qty is not None else "NULL"
            print(f"{inst:<30} {open_str:>15} {closed_str:>15}")
            
        # Summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(closed_quantity) as with_closed_data,
                COUNT(CASE WHEN closed_quantity > 0 THEN 1 END) as with_nonzero_closed
            FROM positions
        """)
        
        total, with_data, nonzero = cursor.fetchone()
        print(f"\nSummary:")
        print(f"  Total positions: {total}")
        print(f"  With closed_quantity data: {with_data}")
        print(f"  With non-zero closed quantities: {nonzero}")
        
    else:
        print("\n✗ closed_quantity column DOES NOT EXIST")
        print("  Need to run migration script first")
    
    conn.close()

if __name__ == "__main__":
    check_closed_quantity() 