#!/usr/bin/env python3
"""Debug market prices database to understand format."""

import sqlite3
import pandas as pd

# Connect to market prices database
conn = sqlite3.connect('data/output/market_prices/market_prices.db')

# Get tables
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Market Prices Database Investigation")
print("=" * 70)
print(f"\nTables found: {[t[0] for t in tables]}")

# Check each table
for table_name in [t[0] for t in tables]:
    print(f"\n\nTable: {table_name}")
    print("-" * 50)
    
    # Get schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
    
    # Get sample data
    query = f"SELECT * FROM {table_name} LIMIT 10"
    df = pd.read_sql_query(query, conn)
    print(f"\nSample data ({len(df)} rows):")
    for idx, row in df.iterrows():
        print(f"  {dict(row)}")
        
    # Check for specific symbols we're looking for
    if 'symbol' in [col[1] for col in columns]:
        print("\nSearching for our symbols...")
        test_patterns = ['%VY3%', '%WY4%', '%OZNQ5%', '%TYQ5%', '%VBYN25%', '%111.25%']
        for pattern in test_patterns:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE symbol LIKE ?", (pattern,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  Found {count} matches for pattern: {pattern}")
                cursor.execute(f"SELECT DISTINCT symbol FROM {table_name} WHERE symbol LIKE ? LIMIT 5", (pattern,))
                for row in cursor.fetchall():
                    print(f"    → {row[0]}")

conn.close() 