import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.market_prices.storage import MarketPriceStorage
from lib.trading.market_prices.options_processor import OptionsProcessor
import logging

logging.basicConfig(level=logging.INFO)

# Initialize storage and processor
storage = MarketPriceStorage("../data/output/market_prices/market_prices.db")
processor = OptionsProcessor(storage)

# Process the July 18th 2pm options file
file_path = Path(r"Z:\Trade_Control\options\Options_20250718_1404.csv")
print(f"Processing {file_path}")
success = processor.process_file(file_path)
print(f"Success: {success}")

# Check the results
import sqlite3
conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check if 3MN5P options now have Flash_Close
cursor.execute("""
    SELECT symbol, Flash_Close, prior_close 
    FROM options_prices 
    WHERE trade_date = '2025-07-18' 
    AND symbol LIKE '3MN5P%'
    ORDER BY symbol
    LIMIT 5
""")
print("\n3MN5P options after processing:")
for row in cursor.fetchall():
    print(f"  {row[0]}: Flash={row[1]}, Prior={row[2]}")

# Count total updates
cursor.execute("""
    SELECT COUNT(*) FROM options_prices 
    WHERE trade_date = '2025-07-18' AND Flash_Close IS NOT NULL
""")
updated_count = cursor.fetchone()[0]
print(f"\nTotal options with Flash_Close on July 18: {updated_count}")

conn.close() 