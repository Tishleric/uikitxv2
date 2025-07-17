#!/usr/bin/env python3
"""Quick inspection of market_prices database schema."""
import sqlite3
from pathlib import Path

def inspect_market_prices():
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data/output/market_prices/market_prices.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in market_prices.db:")
    for (table_name,) in tables:
        print(f"\n{table_name}:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show a sample row
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"\n  Sample row: {sample}")
    
    conn.close()

if __name__ == "__main__":
    inspect_market_prices() 