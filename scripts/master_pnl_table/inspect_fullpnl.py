#!/usr/bin/env python3
"""
inspect_fullpnl.py

Inspect the FULLPNL table to see current structure and data.
"""

import sqlite3
import os


def inspect_fullpnl():
    """Inspect FULLPNL table structure and contents."""
    
    # Database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(project_root, "data", "output", "pnl", "pnl_tracker.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get table structure
        print("FULLPNL Table Structure:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(FULLPNL)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<20} {col[2]:<15} {'PRIMARY KEY' if col[5] else ''}")
        
        # Get all data
        print("\nAll Data in FULLPNL:")
        print("=" * 60)
        cursor.execute("SELECT * FROM FULLPNL ORDER BY symbol")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(FULLPNL)")
        col_info = cursor.fetchall()
        col_names = [col[1] for col in col_info]
        
        # Print header
        print(f"  {'Symbol':<30} {'Bid':>10} {'Ask':>10} {'Price':>10} {'PX Last':>10}")
        print("  " + "-" * 76)
        
        for row in rows:
            row_dict = dict(zip(col_names, row))
            bid = row_dict.get('bid')
            ask = row_dict.get('ask')
            price = row_dict.get('price')
            px_last = row_dict.get('px_last')
            bid_str = f"{bid:.6f}" if bid is not None else "NULL"
            ask_str = f"{ask:.6f}" if ask is not None else "NULL"
            price_str = f"{price:.6f}" if price is not None else "NULL"
            px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
            print(f"  {row_dict['symbol']:<30} {bid_str:>10} {ask_str:>10} {price_str:>10} {px_last_str:>10}")
        
        # Categorize symbols
        print("\nSymbol Categories:")
        print("-" * 60)
        
        # Futures
        cursor.execute("""
            SELECT symbol FROM FULLPNL 
            WHERE symbol NOT LIKE '%P %' AND symbol NOT LIKE '%C %'
            ORDER BY symbol
        """)
        futures = cursor.fetchall()
        print(f"Futures ({len(futures)}):")
        for f in futures:
            print(f"  {f[0]}")
        
        # Options
        cursor.execute("""
            SELECT symbol FROM FULLPNL 
            WHERE symbol LIKE '%P %' OR symbol LIKE '%C %'
            ORDER BY symbol
        """)
        options = cursor.fetchall()
        print(f"\nOptions ({len(options)}):")
        for o in options:
            print(f"  {o[0]}")
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    inspect_fullpnl() 