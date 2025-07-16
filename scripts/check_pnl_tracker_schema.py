#!/usr/bin/env python
"""Check the schema of pnl_tracker.db to see if it has position_tracking table."""

import sqlite3
from pathlib import Path

db_path = Path("data/output/pnl/pnl_tracker.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

print(f"Tables in {db_path.name}:")
for table in tables:
    print(f"  - {table}")

# Check for position_tracking specifically
if 'position_tracking' in tables:
    print("\nposition_tracking table exists!")
    cursor.execute("PRAGMA table_info(position_tracking)")
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("\nWARNING: position_tracking table NOT FOUND!")
    print("The UnifiedPnLService expects this table.")
    
    # Check if there's a positions table instead
    if 'positions' in tables:
        print("\nFound 'positions' table instead:")
        cursor.execute("PRAGMA table_info(positions)")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM positions")
        count = cursor.fetchone()[0]
        print(f"\nRows in positions table: {count}")

conn.close() 