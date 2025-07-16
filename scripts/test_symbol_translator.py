"""Test the SymbolTranslator with actual positions."""

import sys
sys.path.append('.')
import sqlite3
from lib.trading.symbol_translator import SymbolTranslator

print("=== TESTING SYMBOL TRANSLATOR ===\n")

# Get positions from database
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT instrument_name FROM positions ORDER BY instrument_name")
instruments = [row[0] for row in cursor.fetchall()]

translator = SymbolTranslator()

print(f"Testing {len(instruments)} instruments:\n")

success_count = 0
for inst in instruments:
    bloomberg = translator.translate(inst)
    if bloomberg:
        success_count += 1
        print(f"✓ {inst}")
        print(f"  → {bloomberg}")
        
        # Check if this Bloomberg symbol exists in market_prices
        # Extract just the symbol part (first word)
        symbol_part = bloomberg.split()[0]
        cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg = ?", (symbol_part,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ✓ Found {count} price records in database")
        else:
            print(f"  ❌ No price records found for {symbol_part}")
    else:
        print(f"❌ {inst}")
        print(f"  → Translation failed")
    print()

print(f"\nSUMMARY: {success_count}/{len(instruments)} instruments translated successfully")

# Show some Bloomberg symbols in the database for comparison
print("\n\nSample Bloomberg symbols in market_prices table:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE asset_type = 'OPTION' LIMIT 10")
for row in cursor.fetchall():
    print(f"  • {row[0]}")

conn.close() 