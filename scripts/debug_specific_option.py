"""Debug why a specific option price isn't being found."""

import sys
sys.path.append('.')
import sqlite3
from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.pnl_calculator.storage import PnLStorage
from datetime import datetime

# Test with a specific option
test_instrument = "XCMEOCADPS20250714N0VY2/110.75"
print(f"=== DEBUGGING PRICE LOOKUP FOR {test_instrument} ===\n")

# Step 1: Translate the symbol
translator = SymbolTranslator()
bloomberg_symbol = translator.translate(test_instrument)
print(f"1. Symbol translation:")
print(f"   {test_instrument} → {bloomberg_symbol}")

# Step 2: Check if this exact symbol exists in market_prices
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

print(f"\n2. Looking for exact match in market_prices:")
cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg = ?", (bloomberg_symbol,))
count = cursor.fetchone()[0]
print(f"   Found {count} records with bloomberg = '{bloomberg_symbol}'")

# Step 3: Try partial matches
print(f"\n3. Looking for partial matches:")
if bloomberg_symbol:
    # Try just the base symbol
    base_symbol = bloomberg_symbol.split()[0]
    cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg LIKE ?", (f"{base_symbol}%",))
    count = cursor.fetchone()[0]
    print(f"   Found {count} records starting with '{base_symbol}'")
    
    # Show some examples
    cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE bloomberg LIKE ? LIMIT 5", 
                   (f"{base_symbol}%",))
    for row in cursor.fetchall():
        print(f"     • {row[0]}")

# Step 4: Try using the storage method
print(f"\n4. Testing storage.get_market_price:")
storage = PnLStorage("data/output/pnl/pnl_tracker.db")
price, source = storage.get_market_price(test_instrument, datetime.now())
print(f"   Result: price={price}, source={source}")

# Step 5: Look for options with 110.75 strike
print(f"\n5. Looking for any options with 110.75 strike:")
cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE '%110.75%' 
    LIMIT 10
""")
matches = cursor.fetchall()
print(f"   Found {len(matches)} matches:")
for row in matches:
    print(f"     • {row[0]}")

# Step 6: Show what July 14 options we have
print(f"\n6. Checking what July 14 (N25) options exist:")
cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE '%N25%' 
    AND bloomberg LIKE '%110%'
    ORDER BY bloomberg
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"   • {row[0]}")

conn.close()

print("\n\nCONCLUSION:")
print("If the exact Bloomberg symbol isn't found, it could be because:")
print("1. The price file doesn't contain that specific strike")
print("2. The symbol format doesn't match exactly") 
print("3. The price data hasn't been loaded for that date/time") 