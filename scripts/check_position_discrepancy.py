"""
Script to investigate the -15 position discrepancy for TYU5 Comdty
"""

import sqlite3
import pandas as pd
from datetime import datetime

# Connect to database
conn = sqlite3.connect('trades.db')

# Check all TYU5 trades in trades_fifo
print("=== All TYU5 trades in trades_fifo ===")
query = """
SELECT 
    sequenceId,
    time,
    buySell,
    quantity,
    CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END as position_impact
FROM trades_fifo
WHERE symbol = 'TYU5 Comdty'
ORDER BY time
"""
trades_df = pd.read_sql_query(query, conn)
print(trades_df)
print(f"\nTotal open position: {trades_df['position_impact'].sum()}")

# Check trades after August 5th 4pm
print("\n=== Trades after August 5th 4pm ===")
query_after = """
SELECT 
    sequenceId,
    time,
    buySell,
    quantity,
    CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END as position_impact
FROM trades_fifo
WHERE symbol = 'TYU5 Comdty'
  AND datetime(time) > datetime('2025-08-05 16:00:00')
ORDER BY time
"""
after_df = pd.read_sql_query(query_after, conn)
print(after_df)
print(f"\nPosition impact after 4pm: {after_df['position_impact'].sum() if not after_df.empty else 0}")

# Check for duplicate trades
print("\n=== Check for duplicate sequence IDs ===")
dup_query = """
SELECT sequenceId, COUNT(*) as count
FROM trades_fifo
WHERE symbol = 'TYU5 Comdty'
GROUP BY sequenceId
HAVING COUNT(*) > 1
"""
dups = pd.read_sql_query(dup_query, conn)
if dups.empty:
    print("No duplicate sequence IDs found")
else:
    print("Duplicate sequence IDs found:")
    print(dups)

# Compare with realized trades to understand the full picture
print("\n=== Summary of closed positions on August 5th ===")
realized_query = """
SELECT 
    COUNT(*) as trade_count,
    SUM(ABS(quantity)) as total_closed_qty
FROM realized_fifo
WHERE symbol = 'TYU5 Comdty'
  AND DATE(timestamp, 
       CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
            THEN '+1 day' 
            ELSE '+0 day' 
       END) = '2025-08-05'
"""
realized = pd.read_sql_query(realized_query, conn)
print(realized)

conn.close()