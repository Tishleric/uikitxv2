#!/usr/bin/env python
"""Check processed trades in pnl_tracker.db."""

import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("data/output/pnl/pnl_tracker.db")
conn = sqlite3.connect(str(db_path))

# Check processed_trades
print("PROCESSED TRADES:")
df = pd.read_sql_query("""
    SELECT * FROM processed_trades 
    ORDER BY trade_timestamp DESC 
    LIMIT 10
""", conn)

if not df.empty:
    print(f"Found {len(df)} trades (showing first 10)")
    print("\nColumns:", df.columns.tolist())
    print("\nSample data:")
    print(df.to_string())
else:
    print("No trades found")

# Check if positions were calculated
print("\n\nPOSITIONS:")
df_pos = pd.read_sql_query("SELECT * FROM positions", conn)
print(f"Found {len(df_pos)} positions")

if not df_pos.empty:
    print(df_pos.to_string())

conn.close() 