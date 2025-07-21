import pandas as pd
import sqlite3
import time
from datetime import datetime

# Test Excel read time
excel_file = 'data/output/pnl/tyu5_pnl_all_20250720_182150.xlsx'

print("Testing Excel read time...")
start = time.time()
xl = pd.ExcelFile(excel_file)
positions_df = xl.parse('Positions')
trades_df = xl.parse('Trades')
end = time.time()
excel_read_time = end - start

print(f"Excel read time: {excel_read_time:.3f}s")
print(f"Positions rows: {len(positions_df)}")
print(f"Trades rows: {len(trades_df)}")

# Test SQLite write time
print("\nTesting SQLite write time...")
conn = sqlite3.connect(':memory:')  # In-memory for testing

# Create tables
conn.execute('''
CREATE TABLE tyu5_positions (
    run_timestamp DATETIME,
    symbol TEXT,
    type TEXT,
    net_quantity REAL,
    avg_entry_price REAL,
    avg_entry_price_32nds TEXT,
    prior_close REAL,
    current_price REAL,
    prior_present_value REAL,
    current_present_value REAL,
    unrealized_pnl REAL,
    unrealized_pnl_current REAL,
    unrealized_pnl_flash REAL,
    unrealized_pnl_close REAL,
    realized_pnl REAL,
    daily_pnl REAL,
    total_pnl REAL,
    attribution_error TEXT
)''')

conn.execute('''
CREATE TABLE tyu5_trades (
    run_timestamp DATETIME,
    trade_id TEXT,
    datetime TEXT,
    symbol TEXT,
    action TEXT,
    quantity REAL,
    price_decimal REAL,
    price_32nds TEXT,
    fees REAL,
    type TEXT,
    realized_pnl REAL,
    counterparty TEXT
)''')

# Test write time
run_timestamp = datetime.now()
start = time.time()

# Add run_timestamp column
positions_df['run_timestamp'] = run_timestamp
trades_df['run_timestamp'] = run_timestamp

# Write to database
positions_df.to_sql('tyu5_positions', conn, if_exists='append', index=False)
trades_df.to_sql('tyu5_trades', conn, if_exists='append', index=False)
conn.commit()

end = time.time()
db_write_time = end - start

print(f"SQLite write time: {db_write_time:.3f}s")

# Compare
print(f"\nTotal Excel approach time: {excel_read_time:.3f}s")
print(f"Direct database write time: {db_write_time:.3f}s")
print(f"Time difference: {excel_read_time - db_write_time:.3f}s")
print(f"Excel approach is {excel_read_time / db_write_time:.1f}x slower")

# Test read-back time
print("\nTesting SQLite read time...")
start = time.time()
pos_read = pd.read_sql("SELECT * FROM tyu5_positions", conn)
trades_read = pd.read_sql("SELECT * FROM tyu5_trades", conn)
end = time.time()
db_read_time = end - start
print(f"SQLite read time: {db_read_time:.3f}s")

conn.close() 