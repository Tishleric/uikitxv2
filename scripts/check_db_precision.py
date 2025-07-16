#!/usr/bin/env python3
"""Check for floating point precision issues in P&L database."""

import sqlite3
from pathlib import Path


def check_database(db_path):
    """Check a database for precision issues."""
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return
        
    print(f"\nChecking: {db_path}")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    # Check trades table if exists
    if 'trades' in tables:
        print("\nTrades table sample:")
        cursor.execute("SELECT * FROM trades LIMIT 5")
        cols = [desc[0] for desc in cursor.description]
        print(f"Columns: {cols}")
        for row in cursor.fetchall():
            print(row)
    
    # Check trades_processed if exists
    if 'trades_processed' in tables:
        print("\nTrades processed table:")
        cursor.execute("SELECT symbol, quantity, price FROM trades_processed WHERE price IS NOT NULL LIMIT 10")
        for row in cursor.fetchall():
            symbol, qty, price = row
            print(f"{symbol}: qty={qty}, price={price} (repr: {repr(price)})")
            
            # Check for precision issues
            if price and '.' in str(price):
                decimal_places = len(str(price).split('.')[1])
                if decimal_places > 7:
                    print(f"  ⚠️  Precision issue: {decimal_places} decimal places")
    
    # Check position-related tables
    for table in ['positions', 'position_snapshots', 'position_history']:
        if table in tables:
            print(f"\n{table} table:")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [(row[1], row[2]) for row in cursor.fetchall()]
            
            # Find P&L columns
            pnl_cols = [col[0] for col in cols if 'pnl' in col[0].lower() or 'cost' in col[0].lower() or 'price' in col[0].lower()]
            
            if pnl_cols:
                col_list = ', '.join(pnl_cols)
                cursor.execute(f"SELECT {col_list} FROM {table} LIMIT 10")
                
                for row in cursor.fetchall():
                    issues = []
                    for i, val in enumerate(row):
                        if val and isinstance(val, (int, float)):
                            str_val = str(val)
                            if '.' in str_val:
                                decimal_places = len(str_val.split('.')[1])
                                if decimal_places > 7 or 'e' in str_val.lower():
                                    issues.append(f"{pnl_cols[i]}={val} ({decimal_places} decimals)")
                    
                    if issues:
                        print(f"  ⚠️  {', '.join(issues)}")
    
    conn.close()


if __name__ == "__main__":
    # Check both databases
    check_database("data/output/pnl/pnl_tracker_test.db")
    check_database("data/output/pnl/pnl_tracker.db") 