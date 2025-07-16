#!/usr/bin/env python
"""Check the contents of pnl_dashboard.db to see what data exists."""

import sqlite3
import pandas as pd
from pathlib import Path

def check_database_contents():
    """Check what data exists in the P&L dashboard database."""
    db_path = Path("data/output/pnl/pnl_dashboard.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    print(f"Checking database: {db_path}")
    print(f"Database size: {db_path.stat().st_size:,} bytes")
    print("\n" + "="*60 + "\n")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} rows")
    
    print("\n" + "="*60 + "\n")
    
    # Check specific tables for data
    
    # 1. Positions
    print("POSITION TRACKING:")
    try:
        df = pd.read_sql_query("SELECT * FROM position_tracking LIMIT 5", conn)
        print(f"Sample positions ({len(df)} shown):")
        if not df.empty:
            print(df.to_string())
        else:
            print("  No positions found")
    except Exception as e:
        print(f"  Error reading positions: {e}")
    
    print("\n" + "-"*60 + "\n")
    
    # 2. Processed trades
    print("PROCESSED TRADES:")
    try:
        df = pd.read_sql_query("""
            SELECT symbol, trade_time, action, quantity, price 
            FROM processed_trades 
            ORDER BY trade_time DESC 
            LIMIT 5
        """, conn)
        print(f"Recent trades ({len(df)} shown):")
        if not df.empty:
            print(df.to_string())
        else:
            print("  No trades found")
    except Exception as e:
        print(f"  Error reading trades: {e}")
    
    print("\n" + "-"*60 + "\n")
    
    # 3. Price snapshots
    print("PRICE SNAPSHOTS:")
    try:
        df = pd.read_sql_query("""
            SELECT symbol, snapshot_timestamp, price_type, price 
            FROM price_snapshots 
            ORDER BY snapshot_timestamp DESC 
            LIMIT 5
        """, conn)
        print(f"Recent prices ({len(df)} shown):")
        if not df.empty:
            print(df.to_string())
        else:
            print("  No prices found")
    except Exception as e:
        print(f"  Error reading prices: {e}")
    
    print("\n" + "-"*60 + "\n")
    
    # 4. P&L snapshots
    print("P&L SNAPSHOTS:")
    try:
        df = pd.read_sql_query("""
            SELECT symbol, snapshot_date, snapshot_type, realized_pnl, unrealized_pnl 
            FROM pnl_snapshots 
            ORDER BY snapshot_date DESC 
            LIMIT 5
        """, conn)
        print(f"Recent P&L snapshots ({len(df)} shown):")
        if not df.empty:
            print(df.to_string())
        else:
            print("  No P&L snapshots found")
    except Exception as e:
        print(f"  Error reading P&L: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_database_contents() 