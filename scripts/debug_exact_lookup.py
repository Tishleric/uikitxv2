"""Debug the exact price lookup issue."""

import sys
sys.path.append('.')
from lib.trading.pnl_calculator.storage import PnLStorage
from datetime import datetime
import sqlite3

instrument = "XCMEOCADPS20250714N0VY2/110.75"
bloomberg_target = "VBYN25C2 110.750 Comdty"

print(f"Testing price lookup for: {instrument}")
print(f"Should map to: {bloomberg_target}\n")

# Test the storage method
storage = PnLStorage("data/output/pnl/pnl_tracker.db")

# First, test mapping
mapped = storage._map_to_bloomberg(instrument)
print(f"1. _map_to_bloomberg result: {mapped}")
print(f"   Matches expected? {mapped == bloomberg_target}\n")

# Direct query test
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

# Check exact match
print("2. Direct query test:")
cursor.execute("SELECT * FROM market_prices WHERE bloomberg = ? LIMIT 1", (bloomberg_target,))
result = cursor.fetchone()
if result:
    print(f"   Found record!")
    # Get column names
    cursor.execute("PRAGMA table_info(market_prices)")
    columns = [col[1] for col in cursor.fetchall()]
    for i, col in enumerate(columns):
        print(f"   {col}: {result[i]}")
else:
    print(f"   No record found for exact match: '{bloomberg_target}'")

# Now test the actual get_market_price method
print("\n3. Testing get_market_price method:")
price, source = storage.get_market_price(instrument, datetime.now())
print(f"   Result: price={price}, source={source}")

conn.close() 