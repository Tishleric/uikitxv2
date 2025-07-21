#!/usr/bin/env python3
"""Check symbol formats in market prices database."""

import sqlite3
import pandas as pd

# Connect to market prices database
conn = sqlite3.connect('data/output/market_prices/market_prices.db')

# Get sample of symbols
query = """
SELECT DISTINCT symbol 
FROM market_prices 
WHERE symbol LIKE '%N5%' OR symbol LIKE '%N25%'
ORDER BY symbol
LIMIT 50
"""

df = pd.read_sql_query(query, conn)
conn.close()

print("Market Prices Symbol Formats:")
print("=" * 50)
for symbol in df['symbol']:
    print(f"  {symbol}")

print(f"\nTotal found: {len(df)}")

# Also check for specific symbols we're generating
test_symbols = [
    'VY3N5 111.25 Comdty',
    'VBYN25P3 111.25 Comdty', 
    'WY4N5 111.5 Comdty',
    'WBYN25P4 111.5 Comdty',
    'ZN4N5 110.75 Comdty',
    'TYN25P4 110.75 Comdty'
]

conn = sqlite3.connect('data/output/market_prices/market_prices.db')
print("\nChecking for our generated symbols:")
print("=" * 50)
for symbol in test_symbols:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_prices WHERE symbol = ?", (symbol,))
    count = cursor.fetchone()[0]
    print(f"  {symbol:<30} {'✓ FOUND' if count > 0 else '✗ NOT FOUND'}")
conn.close() 