#!/usr/bin/env python
"""Check the contents of pnl_tracker.db."""

import sqlite3
from pathlib import Path

db_path = Path("data/output/pnl/pnl_tracker.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"Database: {db_path}")
print(f"Size: {db_path.stat().st_size:,} bytes")
print(f"\nTables:")

for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  - {table_name}: {count} rows")

# Check if position_tracking exists and has data
if any(t[0] == 'position_tracking' for t in tables):
    print("\nSample positions:")
    cursor.execute("SELECT symbol, quantity, avg_price FROM position_tracking LIMIT 5")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} @ ${row[2]}")

conn.close() 