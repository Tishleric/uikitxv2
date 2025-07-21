#!/usr/bin/env python3
"""Check Bloomberg symbols in market prices database."""

import sqlite3

conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check for our specific Bloomberg symbols
print("Checking for Bloomberg symbols in options_prices:")
print("=" * 60)

test_symbols = [
    'VBYN25P3 111.25 Comdty',  # What we generate
    'WBYN25P4 111.5 Comdty',
    'TYQ5P 110.75 Comdty',
    'VBYN25P3 111.250 Comdty',  # Maybe with different decimal format?
]

for symbol in test_symbols:
    cursor.execute("SELECT COUNT(*) FROM options_prices WHERE symbol = ?", (symbol,))
    count = cursor.fetchone()[0]
    print(f"{symbol:<30} {'✓ FOUND' if count > 0 else '✗ NOT FOUND'}")

# Check what VBY symbols actually exist
print("\nActual VBY symbols in database:")
cursor.execute("SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE 'VBY%' LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check what TY symbols exist  
print("\nActual TY symbols in database:")
cursor.execute("SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE 'TY%' LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check format patterns
print("\nSymbol format analysis:")
cursor.execute("SELECT DISTINCT symbol FROM options_prices LIMIT 20")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close() 