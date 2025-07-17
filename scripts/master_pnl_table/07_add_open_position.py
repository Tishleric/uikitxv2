#!/usr/bin/env python3
"""
Add open_position column to FULLPNL table.
Populates with position_quantity from positions table.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def add_open_position_column():
    """Add open_position column to FULLPNL table and populate from positions."""
    
    # Database paths - go up two levels to project root
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    if not pnl_db_path.exists():
        print(f"Error: P&L database not found at {pnl_db_path}")
        return
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(FULLPNL)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'open_position' not in columns:
            print("Adding open_position column to FULLPNL table...")
            cursor.execute("ALTER TABLE FULLPNL ADD COLUMN open_position REAL")
            conn.commit()
            print("✓ open_position column added")
        else:
            print("open_position column already exists")
        
        # Get all symbols from FULLPNL
        cursor.execute("SELECT symbol FROM FULLPNL")
        symbols = cursor.fetchall()
        print(f"\nProcessing {len(symbols)} symbols...")
        
        updated_count = 0
        missing_count = 0
        zero_position_count = 0
        
        for (symbol,) in symbols:
            print(f"\nProcessing: {symbol}")
            
            # Query positions table for this symbol
            cursor.execute("""
                SELECT position_quantity 
                FROM positions 
                WHERE instrument_name = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            
            if result:
                position = result[0]
                if position is not None:
                    cursor.execute("""
                        UPDATE FULLPNL 
                        SET open_position = ?
                        WHERE symbol = ?
                    """, (position, symbol))
                    
                    if position == 0:
                        print(f"  Found position: {position} (closed)")
                        zero_position_count += 1
                    else:
                        print(f"  Found position: {position}")
                    updated_count += 1
                else:
                    print(f"  ⚠ Position is NULL in positions table")
                    missing_count += 1
            else:
                print(f"  ⚠ Symbol not found in positions table")
                missing_count += 1
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - open_position Column Population:")
        print(f"{'='*60}")
        print(f"Total symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        print(f"  - With non-zero positions: {updated_count - zero_position_count}")
        print(f"  - With zero positions (closed): {zero_position_count}")
        print(f"Missing data: {missing_count} ({missing_count/len(symbols)*100:.1f}%)")
        
        # Show final table state
        print(f"\n{'='*60}")
        print("FULLPNL Table with open_position:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, bid, ask, price, px_last, px_settle, open_position
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'Bid':>10} {'Ask':>10} {'Price':>10} {'px_last':>10} {'px_settle':>10} {'Position':>10}")
        print("-" * 100)
        
        # Print data
        for row in results:
            symbol, bid, ask, price, px_last, px_settle, position = row
            bid_str = f"{bid:.6f}" if bid is not None else "NULL"
            ask_str = f"{ask:.6f}" if ask is not None else "NULL"
            price_str = f"{price:.6f}" if price is not None else "NULL"
            px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
            px_settle_str = f"{px_settle:.6f}" if px_settle is not None else "NULL"
            position_str = f"{position:.1f}" if position is not None else "NULL"
            
            print(f"{symbol:<30} {bid_str:>10} {ask_str:>10} {price_str:>10} {px_last_str:>10} {px_settle_str:>10} {position_str:>10}")
        
        # Check positions table for additional info
        print(f"\n{'='*60}")
        print("Positions Table Overview:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN position_quantity != 0 THEN 1 END) as open_positions,
                   COUNT(CASE WHEN position_quantity = 0 THEN 1 END) as closed_positions
            FROM positions
        """)
        
        total, open_pos, closed_pos = cursor.fetchone()
        print(f"Total positions in positions table: {total}")
        print(f"  - Open positions (non-zero): {open_pos}")
        print(f"  - Closed positions (zero): {closed_pos}")
        
        # Show any positions not in FULLPNL
        cursor.execute("""
            SELECT instrument_name, position_quantity 
            FROM positions 
            WHERE instrument_name NOT IN (SELECT symbol FROM FULLPNL)
        """)
        
        missing_positions = cursor.fetchall()
        if missing_positions:
            print(f"\nPositions in positions table but not in FULLPNL:")
            for inst, qty in missing_positions:
                print(f"  {inst}: {qty}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Adding open_position column to FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    add_open_position_column() 