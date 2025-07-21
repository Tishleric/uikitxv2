#!/usr/bin/env python3
"""Check if put options exist in market prices database."""

import sqlite3

conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("Checking for PUT options in database:")
print("=" * 60)

# Check for puts
cursor.execute("""
SELECT DISTINCT symbol 
FROM options_prices 
WHERE symbol LIKE 'VBYN25P%' 
   OR symbol LIKE 'WBYN25P%' 
   OR symbol LIKE 'TYWN25P%'
   OR symbol LIKE 'TYQ5P%'
   OR symbol LIKE '3MN5P%'
ORDER BY symbol
LIMIT 30
""")

results = cursor.fetchall()
if results:
    print(f"\nFound {len(results)} put options:")
    for row in results:
        print(f"  {row[0]}")
else:
    print("\nNO PUT OPTIONS FOUND!")
    
    # Check what's actually there
    print("\nChecking all option symbols...")
    cursor.execute("SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '%P %' LIMIT 10")
    results = cursor.fetchall()
    if results:
        print("Found these puts:")
        for row in results:
            print(f"  {row[0]}")
    else:
        print("No puts found with 'P ' pattern either!")

conn.close() 