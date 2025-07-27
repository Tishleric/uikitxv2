#!/usr/bin/env python3
"""Check daily positions table in trades.db"""

import sqlite3
import pandas as pd
from pathlib import Path

# Database path
db_path = Path('lib/trading/pnl_fifo_lifo/trades.db')

if not db_path.exists():
    print(f"Database not found at: {db_path}")
    # Try current directory too
    alt_path = Path('trades.db')
    if alt_path.exists():
        print(f"Found database at: {alt_path}")
        db_path = alt_path
    else:
        print("No database found!")
        exit(1)

# Connect and check
conn = sqlite3.connect(db_path)

# Check tables
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("Tables in database:")
print(tables)

# Check daily_positions
try:
    daily_pos = pd.read_sql_query("SELECT * FROM daily_positions ORDER BY date, method", conn)
    print(f"\nDaily positions table has {len(daily_pos)} rows")
    
    if not daily_pos.empty:
        print("\nDaily positions data:")
        print(daily_pos)
    else:
        print("\nDaily positions table is EMPTY")
        
    # Check other tables for comparison
    for method in ['fifo', 'lifo']:
        trades = pd.read_sql_query(f"SELECT COUNT(*) as count FROM trades_{method}", conn)
        realized = pd.read_sql_query(f"SELECT COUNT(*) as count FROM realized_{method}", conn)
        print(f"\n{method.upper()}: {trades['count'][0]} trades, {realized['count'][0]} realized")
        
except Exception as e:
    print(f"Error checking daily_positions: {e}")

conn.close() 