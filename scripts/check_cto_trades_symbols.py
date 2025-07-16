import sqlite3
import pandas as pd
from pathlib import Path

# Connect to the P&L database
db_path = Path("data/output/pnl/pnl_tracker.db")
conn = sqlite3.connect(str(db_path))

# Query to examine symbols and types
query = """
SELECT DISTINCT Symbol, Type 
FROM cto_trades 
ORDER BY Symbol
"""

df = pd.read_sql_query(query, conn)
print("Unique Symbol/Type combinations in cto_trades:")
print(df.to_string(index=False))

# Also show a few complete records
print("\n\nSample complete records:")
query2 = """
SELECT Symbol, Type, Action, Quantity, Price 
FROM cto_trades 
LIMIT 5
"""
df2 = pd.read_sql_query(query2, conn)
print(df2.to_string(index=False))

conn.close() 