"""Final summary of P&L tracking system status."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime

print("=== P&L TRACKING SYSTEM SUMMARY ===")
print(f"Time: {datetime.now()}\n")

# Check database
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

# 1. Trades
cursor.execute("SELECT COUNT(*) FROM processed_trades")
trade_count = cursor.fetchone()[0]
print(f"1. TRADES: {trade_count} processed")

# 2. Positions
cursor.execute("SELECT COUNT(*) FROM positions")
pos_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM positions WHERE last_market_price IS NOT NULL")
priced_count = cursor.fetchone()[0]
print(f"\n2. POSITIONS: {pos_count} total")
print(f"   • {priced_count} with market prices")
print(f"   • {pos_count - priced_count} without prices")

# 3. Show working positions
print("\n3. POSITIONS WITH PRICES:")
cursor.execute("""
    SELECT instrument_name, position_quantity, avg_cost, 
           last_market_price, unrealized_pnl
    FROM positions 
    WHERE last_market_price IS NOT NULL
""")
for row in cursor.fetchall():
    print(f"   • {row[0]}")
    print(f"     Position: {row[1]}, Avg Cost: {row[2]:.5f}")
    print(f"     Market Price: {row[3]:.5f}, Unrealized P&L: ${row[4]:.2f}")

# 4. P&L Summary
cursor.execute("""
    SELECT 
        SUM(total_realized_pnl) as total_realized,
        SUM(unrealized_pnl) as total_unrealized
    FROM positions
""")
result = cursor.fetchone()
total_realized = result[0] or 0
total_unrealized = result[1] or 0

print(f"\n4. P&L SUMMARY:")
print(f"   • Total Realized P&L: ${total_realized:.2f}")
print(f"   • Total Unrealized P&L: ${total_unrealized:.2f}")
print(f"   • Total P&L: ${total_realized + total_unrealized:.2f}")

# 5. Issues
print("\n5. KNOWN ISSUES:")
print("   • Option price mapping incomplete (need proper Bloomberg symbol mapping)")
print("   • Many option prices show '#N/A Requesting Data...' in source files")
print("   • Symbol translator needs to be implemented properly")

print("\n6. WHAT'S WORKING:")
print("   ✅ Trade processing from CSV files")
print("   ✅ Position tracking with FIFO methodology")
print("   ✅ Futures price mapping (e.g., XCMEFFDPSX20250919U0ZN → TU)")
print("   ✅ Unrealized P&L calculation for instruments with prices")
print("   ✅ UI displays positions (though most lack prices)")

conn.close()

print("\n=== END OF SUMMARY ===") 