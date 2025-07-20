import sqlite3
import pandas as pd

# Check TYU5 in cto_trades
conn = sqlite3.connect('../data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

print("=== TYU5 in CTO Trades ===")
cursor.execute("""
    SELECT Symbol, Type, Action, Quantity, Price, Date
    FROM cto_trades 
    WHERE Symbol LIKE '%TYU5%'
    ORDER BY Date, Time
""")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()

# Check TYU5 in market prices
conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("\n=== TYU5 in Market Prices ===")
cursor.execute("""
    SELECT symbol, Flash_Close, prior_close, trade_date
    FROM futures_prices 
    WHERE symbol = 'TYU5'
    AND trade_date >= '2025-07-17'
    ORDER BY trade_date
""")
for row in cursor.fetchall():
    print(f"  {row}")

# Check 3MN5P classification
print("\n=== 3MN5P in CTO Trades ===")
conn2 = sqlite3.connect('../data/output/pnl/pnl_tracker.db')
cursor2 = conn2.cursor()

cursor2.execute("""
    SELECT Symbol, Type, Action, Quantity, Price
    FROM cto_trades 
    WHERE Symbol LIKE '%3MN5P%'
""")
for row in cursor2.fetchall():
    print(f"  {row}")

cursor2.close()
conn2.close()

# Also check why TYU5 shows as "TYU5 Comdty" in output
print("\n=== Symbol Format Check ===")
# The issue might be that the TYU5 adapter is adding " Comdty" suffix
print("In CTO trades: 'TYU5'")
print("In market prices: 'TYU5'")
print("In flash P&L output: 'TYU5 Comdty'")
print("This suffix might be causing the price lookup to fail!")

conn.close() 