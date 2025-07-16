"""Price Step 4: Trace instrument name to Bloomberg symbol mapping."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime

print("=== PRICE STEP 4: TRACING INSTRUMENT NAME MAPPING ===")
print(f"Time: {datetime.now()}\n")

# 1. Show what we have in positions vs market_prices
print("1. INSTRUMENT NAME EXAMPLES:")
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

print("   Position instruments:")
cursor.execute("SELECT DISTINCT instrument_name FROM positions LIMIT 5")
for row in cursor.fetchall():
    print(f"   • {row[0]}")

print("\n   Market price bloomberg symbols:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE asset_type='FUTURE' LIMIT 5")
for row in cursor.fetchall():
    print(f"   • {row[0]}")

cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE asset_type='OPTION' LIMIT 5")
for row in cursor.fetchall():
    print(f"   • {row[0]}")

# 2. Check if there's a symbol translator
print("\n2. CHECKING SYMBOL TRANSLATION:")
from lib.trading.symbol_translator import SymbolTranslator

translator = SymbolTranslator()

# Test some instruments
test_instruments = [
    "XCMEFFDPSX20250919U0ZN",  # Future
    "XCMEOPADPS20250716N0WY3/111.25",  # Option
    "XCMEOCADPS20250714N0VY2/110"  # Option
]

for inst in test_instruments:
    print(f"\n   Translating: {inst}")
    try:
        # Try both directions
        bloomberg = translator.to_bloomberg(inst)
        print(f"   → Bloomberg: {bloomberg}")
        
        # Try reverse
        back = translator.to_internal(bloomberg)
        print(f"   ← Internal: {back}")
    except Exception as e:
        print(f"   ❌ Translation error: {e}")

# 3. Look at storage.get_market_price implementation
print("\n3. ANALYZING get_market_price METHOD:")
print("   Looking at how prices are queried...")

# First check what the method expects
from lib.trading.pnl_calculator.storage import PnLStorage
storage = PnLStorage("data/output/pnl/pnl_tracker.db")

# Test with different formats
test_cases = [
    ("XCMEOCADPS20250714N0VY2/110", "Full instrument name"),
    ("110C JUL14", "Option symbol from price file"),
    ("TU", "Simple future symbol"),
    ("FFDPSX20250919U0ZN", "Future without exchange prefix")
]

for symbol, desc in test_cases:
    print(f"\n   Testing {desc}: {symbol}")
    try:
        price, source = storage.get_market_price(symbol, datetime.now())
        if price:
            print(f"   ✓ Found price: {price}")
        else:
            print(f"   ❌ No price found")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# 4. Check what the one working instrument looks like
print("\n4. ANALYZING THE WORKING CASE:")
working_inst = "XCMEOCADPS20250714N0VY2/110"

# Check in positions
cursor.execute("SELECT * FROM positions WHERE instrument_name = ?", (working_inst,))
pos = cursor.fetchone()
if pos:
    print(f"   ✓ Found in positions")
    # Get column names
    col_names = [desc[0] for desc in cursor.description]
    pos_dict = dict(zip(col_names, pos))
    print(f"   Unrealized P&L: {pos_dict.get('unrealized_pnl')}")
    print(f"   Last market price: {pos_dict.get('last_market_price')}")

# Try to find its price
print("\n   Looking for matching price...")
# Try different patterns
patterns = [
    "110C JUL14",
    "110C",
    "%110%JUL14%",
    "%110%"
]

for pattern in patterns:
    cursor.execute("SELECT bloomberg, px_last FROM market_prices WHERE bloomberg LIKE ? LIMIT 1", (pattern,))
    result = cursor.fetchone()
    if result:
        print(f"   ✓ Found with pattern '{pattern}': {result[0]} = {result[1]}")
        break

conn.close()

print("\n✅ PRICE STEP 4 COMPLETE") 