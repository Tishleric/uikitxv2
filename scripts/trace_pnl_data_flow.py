"""Trace the complete data flow from trade files to PnL dashboard."""

import sys
sys.path.append('.')
import os
from datetime import datetime

print("=== PNL DATA FLOW TRACE ===")
print(f"Started at: {datetime.now()}\n")

# Step 1: Check input trade files
print("STEP 1: Checking input trade files...")
trade_dir = "data/input/trade_ledger"
trade_files = [f for f in os.listdir(trade_dir) if f.endswith('.csv') and f.startswith('trades_')]
print(f"Found {len(trade_files)} trade files:")
for f in sorted(trade_files):
    size = os.path.getsize(os.path.join(trade_dir, f))
    print(f"  - {f} ({size} bytes)")

# Read a sample trade file to see the data
if trade_files:
    latest_file = sorted(trade_files)[-1]
    print(f"\nSample from {latest_file}:")
    with open(os.path.join(trade_dir, latest_file), 'r') as f:
        lines = f.readlines()
        print(f"  Headers: {lines[0].strip()}")
        if len(lines) > 1:
            print(f"  First trade: {lines[1].strip()}")

# Step 2: Process trades through TradePreprocessor
print("\n\nSTEP 2: Processing trades through TradePreprocessor...")
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
preprocessor = TradePreprocessor(
    output_dir="data/output/trade_ledger_processed",
    enable_position_tracking=True,
    storage=storage
)

# Process each trade file
for trade_file in sorted(trade_files):
    file_path = os.path.join(trade_dir, trade_file)
    print(f"\nProcessing {trade_file}...")
    try:
        result = preprocessor.process_trade_file(file_path)
        print(f"  Processed {len(result) if result is not None else 0} trades")
    except Exception as e:
        print(f"  ERROR: {e}")

# Step 3: Check what's in the database after processing
print("\n\nSTEP 3: Checking database after processing...")
import sqlite3
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check processed trades
cursor.execute("SELECT COUNT(*) as count FROM processed_trades")
trade_count = cursor.fetchone()['count']
print(f"Total processed trades: {trade_count}")

if trade_count > 0:
    cursor.execute("""
        SELECT trade_date, instrument_name, quantity, price 
        FROM processed_trades 
        ORDER BY trade_date DESC 
        LIMIT 3
    """)
    print("Sample processed trades:")
    for row in cursor.fetchall():
        print(f"  {row['trade_date']} | {row['instrument_name']} | qty={row['quantity']} | price={row['price']}")

# Check positions
cursor.execute("SELECT COUNT(*) as count FROM positions")
pos_count = cursor.fetchone()['count']
print(f"\nTotal positions: {pos_count}")

if pos_count > 0:
    cursor.execute("""
        SELECT instrument_name, position_quantity, total_realized_pnl, unrealized_pnl 
        FROM positions 
        LIMIT 3
    """)
    print("Sample positions:")
    for row in cursor.fetchall():
        print(f"  {row['instrument_name']} | qty={row['position_quantity']} | realized={row['total_realized_pnl']} | unrealized={row['unrealized_pnl']}")

conn.close()

# Step 4: Test UnifiedPnLService
print("\n\nSTEP 4: Testing UnifiedPnLService...")
from lib.trading.pnl_calculator.unified_service import UnifiedPnLService

service = UnifiedPnLService(
    db_path="data/output/pnl/pnl_tracker.db",
    trade_ledger_dir=trade_dir,
    price_directories=[
        "data/input/market_prices/futures",
        "data/input/market_prices/options"
    ]
)

positions = service.get_open_positions()
print(f"UnifiedPnLService returned {len(positions)} positions")
if positions:
    print(f"First position keys: {list(positions[0].keys())}")
    print(f"Sample position: {positions[0]}")

# Step 5: Test DataAggregator
print("\n\nSTEP 5: Testing DataAggregator...")
from lib.trading.pnl_calculator.data_aggregator import PnLDataAggregator

aggregator = PnLDataAggregator(service)
positions_df = aggregator.format_positions_for_display(positions)
print(f"DataAggregator formatted {len(positions_df)} positions")
print(f"DataFrame columns: {list(positions_df.columns)}")
if not positions_df.empty:
    print("\nFirst position after formatting:")
    print(positions_df.iloc[0].to_dict())

# Step 6: Test Controller
print("\n\nSTEP 6: Testing PnLDashboardController...")
from apps.dashboards.pnl_v2.controller import PnLDashboardController

controller = PnLDashboardController()
positions_data = controller.get_positions_data()
print(f"Controller returned {positions_data['count']} positions")
if positions_data['data']:
    print(f"First position from controller: {positions_data['data'][0]}")

print("\n\n=== DATA FLOW TRACE COMPLETE ===")
print(f"Finished at: {datetime.now()}")
print("\nSUMMARY:")
print(f"- Input trade files: {len(trade_files)}")
print(f"- Processed trades in DB: {trade_count}")
print(f"- Positions in DB: {pos_count}")
print(f"- Positions from service: {len(positions)}")
print(f"- Positions from controller: {positions_data['count']}")

if positions_data['count'] == 0 and pos_count > 0:
    print("\n⚠️  ISSUE FOUND: Database has positions but controller returns none!")
    print("   This is likely where the data flow breaks.") 