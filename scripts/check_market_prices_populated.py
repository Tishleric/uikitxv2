#!/usr/bin/env python3
"""Check if market prices database was populated."""

import sqlite3
from pathlib import Path
from datetime import datetime

print("\nMARKET PRICES DATABASE CHECK")
print("=" * 60)

db_path = Path("data/output/market_prices/market_prices.db")
if not db_path.exists():
    print("❌ Database does not exist!")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check futures prices
print("\n1. FUTURES PRICES:")
cursor.execute("""
    SELECT symbol, flash_close, prior_close, last_updated, 
           strftime('%Y-%m-%d %H:%M', last_updated) as update_time
    FROM futures_prices
    ORDER BY symbol
""")
futures = cursor.fetchall()

if futures:
    print(f"   Found {len(futures)} futures contracts:")
    for row in futures:
        symbol, flash, prior, _, update_time = row
        print(f"   - {symbol}: Flash={flash:.4f}, Prior={prior:.4f} (Updated: {update_time})")
else:
    print("   ❌ No futures prices found")

# Check options prices
print("\n2. OPTIONS PRICES:")
cursor.execute("""
    SELECT COUNT(*) as count, 
           MIN(last_updated) as first_update,
           MAX(last_updated) as last_update
    FROM options_prices
""")
count, first, last = cursor.fetchone()

if count > 0:
    print(f"   Found {count} options contracts")
    print(f"   First update: {first}")
    print(f"   Last update: {last}")
    
    # Show a sample
    cursor.execute("""
        SELECT symbol, flash_close, prior_close
        FROM options_prices
        WHERE flash_close IS NOT NULL
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print("\n   Sample options:")
    for symbol, flash, prior in samples:
        print(f"   - {symbol}: Flash={flash:.4f}, Prior={prior:.4f if prior else 'None'}")
else:
    print("   ❌ No options prices found")

conn.close()
print("\n" + "=" * 60) 