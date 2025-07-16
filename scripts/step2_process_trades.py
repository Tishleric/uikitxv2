"""Step 2: Process trade files and check results."""

import sys
sys.path.append('.')
import os
from datetime import datetime

print("=== STEP 2: PROCESSING TRADE FILES ===")
print(f"Time: {datetime.now()}\n")

from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

# Use fresh database
db_path = "data/output/pnl/pnl_tracker.db"
storage = PnLStorage(db_path)

# Create preprocessor with position tracking enabled
preprocessor = TradePreprocessor(
    output_dir="data/output/trade_ledger_processed",
    enable_position_tracking=True,
    storage=storage
)

trade_dir = "data/input/trade_ledger"
trade_files = sorted([f for f in os.listdir(trade_dir) if f.startswith('trades_') and f.endswith('.csv')])

print(f"Processing {len(trade_files)} trade files...\n")

total_trades = 0
for trade_file in trade_files:
    file_path = os.path.join(trade_dir, trade_file)
    print(f"Processing {trade_file}...")
    
    try:
        # Process the file
        result_df = preprocessor.process_trade_file(file_path)
        
        if result_df is not None and not result_df.empty:
            trade_count = len(result_df)
            total_trades += trade_count
            print(f"  ✓ Processed {trade_count} trades")
            
            # Show first trade from this file
            first_trade = result_df.iloc[0]
            print(f"    Sample: {first_trade['instrument_name']} | qty={first_trade['quantity']} | price={first_trade['price']}")
        else:
            print(f"  ⚠️  No trades processed (empty result)")
            
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")

print(f"\n📊 Total trades processed: {total_trades}")

# Check database to confirm trades were saved
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM processed_trades")
db_count = cursor.fetchone()[0]
print(f"📊 Trades in database: {db_count}")

# Show some trades from DB
cursor.execute("""
    SELECT trade_date, instrument_name, quantity, price 
    FROM processed_trades 
    ORDER BY id DESC 
    LIMIT 5
""")
print("\nLatest trades in database:")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} | qty={row[2]} | price={row[3]}")

conn.close()

print("\n✅ STEP 2 COMPLETE: Trades processed and saved to database") 