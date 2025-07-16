#!/usr/bin/env python
"""Check the schema of pnl_dashboard.db."""

import sqlite3
from pathlib import Path

def check_schema():
    """Check the database schema."""
    db_path = Path("data/output/pnl/pnl_dashboard.db")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Database Schema:\n")
    
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")
        print("-" * 40)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            print(f"  {name:20} {dtype:15} {'NOT NULL' if notnull else 'NULL':8} {'PK' if pk else ''}")
        
        print()
    
    conn.close()

if __name__ == "__main__":
    check_schema() 