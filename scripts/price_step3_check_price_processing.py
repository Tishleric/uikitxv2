"""Price Step 3: Check market_prices schema and trace processing."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime

print("=== PRICE STEP 3: CHECKING PRICE PROCESSING ===")
print(f"Time: {datetime.now()}\n")

# 1. Check market_prices table schema
print("1. MARKET_PRICES TABLE SCHEMA:")
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(market_prices)")
columns = cursor.fetchall()
print("   Columns:")
for col in columns:
    print(f"   • {col[1]} ({col[2]})")

# 2. Check what's actually in the table
print("\n2. MARKET_PRICES TABLE CONTENTS:")
cursor.execute("SELECT COUNT(*) FROM market_prices")
count = cursor.fetchone()[0]
print(f"   Total records: {count}")

if count > 0:
    # Get column names dynamically
    cursor.execute("SELECT * FROM market_prices LIMIT 1")
    col_names = [desc[0] for desc in cursor.description]
    
    # Get sample data
    cursor.execute("SELECT * FROM market_prices LIMIT 5")
    rows = cursor.fetchall()
    print("\n   Sample records:")
    for row in rows:
        data = dict(zip(col_names, row))
        print(f"   {data}")

# 3. Process a price file manually to see what happens
print("\n3. MANUAL PRICE FILE PROCESSING:")
from lib.trading.pnl_calculator.service import PnLService
from lib.trading.pnl_calculator.storage import PnLStorage

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
service = PnLService(storage)

# Try processing a futures file
futures_file = "data/input/market_prices/futures/Futures_20250715_1400.csv"
print(f"\n   Processing {futures_file}...")
try:
    service.process_market_price_file(futures_file)
    print("   ✓ Processed successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try processing an options file
options_file = "data/input/market_prices/options/Options_20250715_1400.csv"
print(f"\n   Processing {options_file}...")
try:
    service.process_market_price_file(options_file)
    print("   ✓ Processed successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Check how prices are queried
print("\n4. CHECKING PRICE QUERIES:")
test_instruments = [
    "XCMEOPADPS20250716N0WY3/111.25",
    "XCMEFFDPSX20250919U0ZN",
    "XCMEOCADPS20250714N0VY2/110"  # The one that works
]

for inst in test_instruments:
    print(f"\n   Looking for prices for: {inst}")
    
    # Try the storage method
    try:
        price, source = storage.get_market_price(inst, datetime.now())
        if price:
            print(f"   ✓ Found price: {price} from {source}")
        else:
            print(f"   ❌ No price found")
    except Exception as e:
        print(f"   ❌ Error getting price: {e}")

conn.close()

print("\n✅ PRICE STEP 3 COMPLETE") 