import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.market_prices.storage import MarketPriceStorage
from lib.trading.market_prices.futures_processor import FuturesProcessor
import logging

logging.basicConfig(level=logging.DEBUG)

# Initialize storage and processor
storage = MarketPriceStorage("../data/output/market_prices/market_prices.db")
processor = FuturesProcessor(storage)

# Process the July 18th file
file_path = Path(r"Z:\Trade_Control\futures\Futures_20250718_1404.csv")
print(f"Processing {file_path}")
success = processor.process_file(file_path)
print(f"Success: {success}")

# Check what's in the database now
import sqlite3
conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

cursor.execute("SELECT trade_date, symbol, Flash_Close, prior_close FROM futures_prices WHERE trade_date = '2025-07-18' ORDER BY symbol")
print("\nJuly 18 futures data after processing:")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]}: Flash={row[2]}, Prior={row[3]}")

conn.close() 