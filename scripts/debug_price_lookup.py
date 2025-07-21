#!/usr/bin/env python3
"""Debug why price lookups are failing when data exists."""

import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter

# Test symbols we're looking for
test_symbols = [
    'VY3N5 P 111.25',  # What TYU5 receives
    'VY3N5 P 111.250', # Maybe needs exact decimal?
]

# Expected Bloomberg lookups
expected_bloomberg = [
    'VBYN25P3 111.25 Comdty',
    'VBYN25P3 111.250 Comdty',
]

print("Debug Price Lookup Issue")
print("=" * 70)

# 1. Check what's in database
conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("\n1. Checking database for our symbols:")
for symbol in expected_bloomberg:
    cursor.execute("SELECT COUNT(*) FROM options_prices WHERE symbol = ?", (symbol,))
    count = cursor.fetchone()[0]
    print(f"  {symbol:<30} Count: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM options_prices WHERE symbol = ? LIMIT 1", (symbol,))
        row = cursor.fetchone()
        print(f"    → Data: {row}")

# 2. Check what TYU5Adapter does
print("\n2. Testing TYU5Adapter lookup:")
adapter = TYU5Adapter()

# Get market prices for our symbols
result = adapter.get_market_prices_for_symbols(test_symbols)
print(f"\nResult DataFrame shape: {result.shape}")
print(f"Columns: {result.columns.tolist()}")
print(f"\nData:\n{result}")

# 3. Debug the exact query TYU5Adapter uses
print("\n3. Simulating TYU5Adapter query:")
for symbol in test_symbols:
    print(f"\nProcessing: {symbol}")
    
    # Parse as option (what TYU5Adapter does)
    parts = symbol.split()
    if len(parts) == 3:
        base = parts[0]  # VY3N5
        opt_type = parts[1]  # P
        strike = parts[2]  # 111.25
        
        # TYU5Adapter tries to translate CME symbol
        print(f"  Base: {base}, Type: {opt_type}, Strike: {strike}")
        
        # Build Bloomberg format (what it should do)
        bloomberg = f"{base} {strike} Comdty"
        print(f"  Lookup attempt: {bloomberg}")
        
        cursor.execute("SELECT COUNT(*) FROM options_prices WHERE symbol = ?", (bloomberg,))
        count = cursor.fetchone()[0]
        print(f"  Found in DB: {count}")

conn.close() 