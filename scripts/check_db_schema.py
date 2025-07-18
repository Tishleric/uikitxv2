#!/usr/bin/env python
"""Check database schema."""

import sqlite3

# Connect to database
db_path = "data/output/pnl/pnl_tracker.db"
conn = sqlite3.connect(db_path)

# Get positions table schema
print("POSITIONS TABLE SCHEMA:")
cursor = conn.execute("PRAGMA table_info(positions)")
for col in cursor:
    print(f"  {col[1]} ({col[2]})")

print("\n\nLOT_POSITIONS TABLE SCHEMA:")
cursor = conn.execute("PRAGMA table_info(lot_positions)")
for col in cursor:
    print(f"  {col[1]} ({col[2]})")

conn.close() 