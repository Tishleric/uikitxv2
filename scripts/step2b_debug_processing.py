"""Step 2b: Debug why trades aren't being processed."""

import sys
sys.path.append('.')
import pandas as pd
from datetime import datetime

print("=== STEP 2B: DEBUGGING TRADE PROCESSING ===")
print(f"Time: {datetime.now()}\n")

# First, let's read a trade file directly
trade_file = "data/input/trade_ledger/trades_20250715.csv"
print(f"Reading {trade_file} directly...")

df = pd.read_csv(trade_file)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\nFirst few rows:")
print(df.head())

# Now let's trace through the TradePreprocessor
print("\n\nTracing TradePreprocessor...")
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
preprocessor = TradePreprocessor(
    output_dir="data/output/trade_ledger_processed",
    enable_position_tracking=True,
    storage=storage
)

# Let's manually call the process method step by step
print("\nChecking if file was already processed...")
import sqlite3
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM file_processing_log WHERE file_path = ?", (trade_file,))
log_entry = cursor.fetchone()
if log_entry:
    print(f"  ⚠️  File already in processing log: {log_entry}")
else:
    print("  ✓ File not in processing log")

# Check position manager initialization
print("\nChecking position manager...")
if hasattr(preprocessor, 'position_manager'):
    print(f"  ✓ Position manager exists: {preprocessor.position_manager}")
else:
    print("  ❌ No position manager attribute")

# Try processing with more detail
print("\n\nAttempting detailed processing...")
try:
    # Read the CSV
    df = pd.read_csv(trade_file)
    print(f"  ✓ Read {len(df)} rows from CSV")
    
    # Check required columns
    required_cols = ['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"  ❌ Missing columns: {missing}")
    else:
        print(f"  ✓ All required columns present")
    
    # Process each trade manually
    print("\nProcessing trades individually...")
    for idx, row in df.iterrows():
        print(f"\n  Trade {idx + 1}:")
        print(f"    ID: {row['tradeId']}")
        print(f"    Instrument: {row['instrumentName']}")
        print(f"    Qty: {row['quantity']} ({row['buySell']})")
        print(f"    Price: {row['price']}")
        
        # Create trade data dict
        trade_data = {
            'tradeId': str(row['tradeId']),
            'instrumentName': row['instrumentName'],
            'marketTradeTime': row['marketTradeTime'],
            'quantity': float(row['quantity']) if row['buySell'] == 'B' else -float(row['quantity']),
            'price': float(row['price'])
        }
        
        # Try to process through position manager if it exists
        if hasattr(preprocessor, 'position_manager') and preprocessor.position_manager:
            try:
                result = preprocessor.position_manager.process_trade(trade_data)
                print(f"    ✓ Position update: {result.trade_action} - new qty: {result.new_quantity}")
            except Exception as e:
                print(f"    ❌ Position processing error: {e}")
        
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

conn.close() 