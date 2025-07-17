#!/usr/bin/env python3
"""Show summary of FULLPNL table with all columns."""
import sqlite3
from pathlib import Path

def show_fullpnl_summary():
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    # Get all columns
    cursor.execute("PRAGMA table_info(FULLPNL)")
    columns = cursor.fetchall()
    
    print("FULLPNL Table Structure:")
    print("="*50)
    for col in columns:
        print(f"  {col[1]:<20} {col[2]}")
    
    # Count populated columns for each row
    print(f"\n{'='*50}")
    print("Data Population Summary:")
    print(f"{'='*50}")
    
    # Get all data
    cursor.execute("SELECT * FROM FULLPNL ORDER BY symbol")
    rows = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    for row in rows:
        symbol = row[0]
        populated = sum(1 for val in row[1:] if val is not None)
        total = len(row) - 1  # Exclude symbol column
        print(f"{symbol:<30} {populated}/{total} columns populated ({populated/total*100:.1f}%)")
    
    # Show which columns are fully populated
    print(f"\n{'='*50}")
    print("Column Population Statistics:")
    print(f"{'='*50}")
    
    for i, col_name in enumerate(col_names):
        if col_name == 'symbol':
            continue
        cursor.execute(f"SELECT COUNT({col_name}) FROM FULLPNL")
        count = cursor.fetchone()[0]
        print(f"{col_name:<20} {count}/8 populated ({count/8*100:.1f}%)")
    
    conn.close()

if __name__ == "__main__":
    show_fullpnl_summary() 