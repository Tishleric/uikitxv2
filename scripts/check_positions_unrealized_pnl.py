"""
Check unrealized P&L values in positions table
"""

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('trades.db')

# Query positions with non-zero unrealized P&L
query = """
SELECT 
    symbol,
    open_position,
    closed_position,
    fifo_realized_pnl,
    fifo_unrealized_pnl,
    lifo_unrealized_pnl,
    fifo_unrealized_pnl_close,
    lifo_unrealized_pnl_close,
    last_updated
FROM positions
WHERE fifo_unrealized_pnl != 0 
   OR lifo_unrealized_pnl != 0
   OR open_position != 0
ORDER BY ABS(fifo_unrealized_pnl) DESC
LIMIT 10
"""

df = pd.read_sql_query(query, conn)
conn.close()

print("=" * 80)
print("UNREALIZED P&L VALUES IN POSITIONS TABLE")
print("=" * 80)

if df.empty:
    print("No positions found with unrealized P&L")
else:
    print(f"\nFound {len(df)} positions with data:")
    print(df.to_string(index=False))
    
    # Summary
    print(f"\nSummary:")
    print(f"Total FIFO Unrealized P&L: ${df['fifo_unrealized_pnl'].sum():,.2f}")
    print(f"Total LIFO Unrealized P&L: ${df['lifo_unrealized_pnl'].sum():,.2f}")
    print(f"Total FIFO Close P&L: ${df['fifo_unrealized_pnl_close'].sum():,.2f}")
    print(f"Total LIFO Close P&L: ${df['lifo_unrealized_pnl_close'].sum():,.2f}")