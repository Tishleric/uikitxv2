"""Import clean price CSV files into database."""

import sys
sys.path.append('.')
import pandas as pd
from datetime import datetime
from lib.trading.pnl_calculator.storage import PnLStorage

print("=== IMPORTING CLEAN PRICE FILES ===\n")

storage = PnLStorage("data/output/pnl/pnl_tracker.db")

# Import futures prices
futures_file = "data/input/market_prices/futures/Futures_20250712_1400.csv"
print(f"Reading {futures_file}...")
futures_df = pd.read_csv(futures_file)
print(f"  Rows: {len(futures_df)}")
print(f"  Columns: {list(futures_df.columns)}")

# Create upload timestamp - July 12, 2pm
upload_time = datetime(2025, 7, 12, 14, 0, 0)
saved = storage.save_market_prices(futures_df, upload_time, futures_file)
print(f"  Saved {saved} futures prices\n")

# Import options prices
options_file = "data/input/market_prices/options/Options_20250712_1400.csv"
print(f"Reading {options_file}...")
options_df = pd.read_csv(options_file)
print(f"  Rows: {len(options_df)}")
print(f"  Columns: {list(options_df.columns)}")

saved = storage.save_market_prices(options_df, upload_time, options_file)
print(f"  Saved {saved} options prices\n")

# Verify import
import sqlite3
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM market_prices")
total = cursor.fetchone()[0]
print(f"Total records in market_prices: {total}")

cursor.execute("SELECT COUNT(*) FROM market_prices WHERE asset_type = 'FUTURE'")
futures_count = cursor.fetchone()[0]
print(f"  Futures: {futures_count}")

cursor.execute("SELECT COUNT(*) FROM market_prices WHERE asset_type = 'OPTION'")
options_count = cursor.fetchone()[0]
print(f"  Options: {options_count}")

# Show sample records
print("\nSample futures:")
cursor.execute("SELECT bloomberg, px_settle, px_last FROM market_prices WHERE asset_type = 'FUTURE' LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row[0]}: settle={row[1]}, last={row[2]}")

print("\nSample options:")
cursor.execute("SELECT bloomberg, px_settle, px_last FROM market_prices WHERE asset_type = 'OPTION' AND bloomberg LIKE 'VBYN%' LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row[0]}: settle={row[1]}, last={row[2]}")

conn.close()
print("\n✓ Price import complete!") 