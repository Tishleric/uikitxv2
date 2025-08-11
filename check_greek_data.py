import os
import sqlite3
import pandas as pd

# Check spot_risk.db
spot_risk_path = 'data/output/spot_risk/spot_risk.db'
print(f'spot_risk.db exists: {os.path.exists(spot_risk_path)}')

if os.path.exists(spot_risk_path):
    conn = sqlite3.connect(spot_risk_path)
    
    print('\n=== TABLES IN SPOT_RISK.DB ===')
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print(tables)
    
    print('\n=== SAMPLE SPOT_RISK_CALCULATED DATA ===')
    try:
        query = 'SELECT * FROM spot_risk_calculated LIMIT 10'
        df = pd.read_sql_query(query, conn)
        print(df.to_string())
    except Exception as e:
        print(f'Error: {e}')
    
    conn.close()

# Check if PositionsAggregator is running
print('\n=== CHECKING FOR AGGREGATOR PROCESSES ===')
import psutil
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info.get('cmdline', [])
        if cmdline and any('positions_aggregator' in str(arg).lower() for arg in cmdline):
            print(f"Found aggregator process: PID={proc.info['pid']}, CMD={cmdline}")
    except:
        pass

# Check trades tables
print('\n=== CHECKING TRADES TABLES ===')
conn = sqlite3.connect('trades.db')
query = """
SELECT name FROM sqlite_master 
WHERE type='table' AND name LIKE 'trades_%'
"""
tables = pd.read_sql_query(query, conn)
print(f"Trade tables: {tables['name'].tolist()}")

# Sample trade data
print('\n=== SAMPLE TRADES_FIFO DATA ===')
try:
    query = 'SELECT symbol, buySell, quantity, price FROM trades_fifo LIMIT 10'
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
except Exception as e:
    print(f'Error: {e}')

conn.close()