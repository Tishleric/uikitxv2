"""Check why some symbols are missing from market_prices."""

import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

print("=== CHECKING MISSING SYMBOLS ===\n")

# Check futures
print("Futures in database:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE asset_type = 'FUTURE' ORDER BY bloomberg")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check for TYU5
print("\nLooking for TYU5:")
cursor.execute("SELECT * FROM market_prices WHERE bloomberg LIKE '%TYU5%'")
results = cursor.fetchall()
print(f"  Found {len(results)} matches")

# Check for TY
print("\nLooking for any TY futures:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE bloomberg LIKE '%TY%' AND asset_type = 'FUTURE'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check VBYN options
print("\n\nVBYN options in database:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE bloomberg LIKE 'VBYN%' ORDER BY bloomberg")
vbyn_options = cursor.fetchall()
print(f"  Found {len(vbyn_options)} unique VBYN options")

# Check specifically for missing strikes
missing = ["VBYN25C2 108.750 Comdty", "VBYN25C2 109.000 Comdty"]
for symbol in missing:
    cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg = ?", (symbol,))
    count = cursor.fetchone()[0]
    print(f"  {symbol}: {'FOUND' if count > 0 else 'NOT FOUND'}")

# Show VBYN strikes we do have
print("\nVBYN25C2 strikes available:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE bloomberg LIKE 'VBYN25C2%' ORDER BY bloomberg")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close() 