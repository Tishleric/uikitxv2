"""Step 3: Clear processing state and show open positions."""

import sys
sys.path.append('.')
import os
from datetime import datetime
import sqlite3

print("=== STEP 3: CLEARING STATE AND SHOWING POSITIONS ===")
print(f"Time: {datetime.now()}\n")

# Clear the processing state file
state_file = "data/output/trade_ledger_processed/.processing_state.json"
if os.path.exists(state_file):
    os.remove(state_file)
    print(f"✓ Cleared processing state file: {state_file}")

# Now reprocess all trades
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
preprocessor = TradePreprocessor(
    output_dir="data/output/trade_ledger_processed",
    enable_position_tracking=True,
    storage=storage
)

trade_dir = "data/input/trade_ledger"
trade_files = sorted([f for f in os.listdir(trade_dir) if f.startswith('trades_') and f.endswith('.csv')])

print(f"\nReprocessing {len(trade_files)} trade files...")
total_trades = 0

for trade_file in trade_files:
    file_path = os.path.join(trade_dir, trade_file)
    print(f"\nProcessing {trade_file}...")
    
    result_df = preprocessor.process_trade_file(file_path)
    if result_df is not None and not result_df.empty:
        trade_count = len(result_df)
        total_trades += trade_count
        print(f"  ✓ Processed {trade_count} trades")

print(f"\n📊 Total trades processed: {total_trades}")

# Now show open positions
print("\n\n=== OPEN POSITIONS ===")
print("Positions are calculated using FIFO method\n")

# Get positions directly from position manager
positions = preprocessor.position_manager.get_positions()
print(f"Found {len(positions)} open positions:\n")

if positions:
    # Sort by instrument name
    positions.sort(key=lambda x: x['instrument_name'])
    
    # Print header
    print(f"{'Instrument':<40} {'Quantity':>10} {'Avg Cost':>10} {'Realized P&L':>12} {'Unrealized':>12}")
    print("-" * 90)
    
    total_realized = 0
    total_unrealized = 0
    
    for pos in positions:
        instrument = pos['instrument_name']
        quantity = pos['position_quantity']
        avg_cost = pos['avg_cost']
        realized = pos['total_realized_pnl']
        unrealized = pos['unrealized_pnl']
        
        total_realized += realized
        total_unrealized += unrealized
        
        # Shorten long instrument names
        if len(instrument) > 38:
            instrument = instrument[:35] + "..."
            
        print(f"{instrument:<40} {quantity:>10.2f} {avg_cost:>10.5f} ${realized:>11.2f} ${unrealized:>11.2f}")
    
    print("-" * 90)
    print(f"{'TOTALS':<40} {' ':>10} {' ':>10} ${total_realized:>11.2f} ${total_unrealized:>11.2f}")
    print(f"\n💰 Total P&L: ${total_realized + total_unrealized:,.2f}")

# Also show positions from database
print("\n\n=== VERIFYING DATABASE ===")
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM processed_trades")
trade_count = cursor.fetchone()[0]
print(f"Processed trades in DB: {trade_count}")

cursor.execute("SELECT COUNT(*) FROM positions")
pos_count = cursor.fetchone()[0]
print(f"Positions in DB: {pos_count}")

conn.close()

print("\n✅ STEP 3 COMPLETE: Positions calculated and displayed") 