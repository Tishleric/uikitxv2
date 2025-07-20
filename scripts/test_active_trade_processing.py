#!/usr/bin/env python3
"""
Test the ACTIVE trade processing system by running it on existing trade ledger files.
This simulates what the file watcher would trigger automatically.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from pathlib import Path
import glob
from datetime import datetime

# Import our trade processor
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.storage import PnLStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inspect_csv_files():
    """First, let's inspect the raw CSV files to understand their format."""
    print("\n" + "="*80)
    print("INSPECTING RAW CSV FILES")
    print("="*80 + "\n")
    
    trade_dir = Path("data/input/trade_ledger")
    csv_files = sorted(glob.glob(str(trade_dir / "*.csv")))
    
    for csv_file in csv_files:
        print(f"\n--- {Path(csv_file).name} ---")
        df = pd.read_csv(csv_file)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head())
        print(f"\nUnique instruments: {df['instrumentName'].unique()}")
        
        # Check for SOD and exercised trades
        sod_mask = df['marketTradeTime'].str.contains('00:00:00.000')
        exercised_mask = df['price'].astype(float) == 0.0
        
        print(f"\nSOD trades (midnight): {sod_mask.sum()}")
        print(f"Exercised trades (price=0): {exercised_mask.sum()}")
        
def run_trade_processing():
    """Run the trade processing system and inspect the output."""
    print("\n" + "="*80)
    print("RUNNING TRADE PROCESSING SYSTEM")
    print("="*80 + "\n")
    
    # Initialize the preprocessor
    preprocessor = TradePreprocessor(enable_position_tracking=False)
    
    # Get all CSV files
    trade_dir = Path("data/input/trade_ledger")
    csv_files = sorted(glob.glob(str(trade_dir / "*.csv")))
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process all files
    preprocessor.process_all_trade_files(csv_files)
    
    # Now query the CTO trades table to see what was inserted
    print("\n" + "="*80)
    print("INSPECTING CTO TRADES TABLE")
    print("="*80 + "\n")
    
    storage = PnLStorage()
    conn = storage._get_connection()
    
    # Query all trades from CTO table
    query = """
    SELECT 
        Date, Time, Symbol, Action, Quantity, Price, 
        Fees, Counterparty, tradeID, Type, 
        source_file, is_sod, is_exercise
    FROM cto_trades
    ORDER BY Date, Time
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Total trades in CTO table: {len(df)}")
    print("\nColumn types:")
    print(df.dtypes)
    
    print("\nFirst 10 trades:")
    print(df.head(10).to_string())
    
    print("\nLast 5 trades:")
    print(df.tail(5).to_string())
    
    # Summary statistics
    print("\n" + "-"*40)
    print("SUMMARY STATISTICS")
    print("-"*40)
    print(f"Total trades: {len(df)}")
    print(f"Unique symbols: {df['Symbol'].nunique()}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Futures: {len(df[df['Type'] == 'FUT'])}")
    print(f"Calls: {len(df[df['Type'] == 'CALL'])}")
    print(f"Puts: {len(df[df['Type'] == 'PUT'])}")
    print(f"Buys: {len(df[df['Action'] == 'BUY'])}")
    print(f"Sells: {len(df[df['Action'] == 'SELL'])}")
    
    print("\nUnique symbols:")
    for symbol in sorted(df['Symbol'].unique()):
        count = len(df[df['Symbol'] == symbol])
        symbol_type = df[df['Symbol'] == symbol]['Type'].iloc[0]
        print(f"  {symbol} ({symbol_type}): {count} trades")
    
    # Check for any issues
    print("\n" + "-"*40)
    print("DATA VALIDATION")
    print("-"*40)
    
    # Check for SOD or exercised trades (should be 0)
    sod_count = df['is_sod'].sum()
    exercise_count = df['is_exercise'].sum()
    print(f"SOD trades in output: {sod_count} (should be 0)")
    print(f"Exercised trades in output: {exercise_count} (should be 0)")
    
    # Check for negative quantities (should be 0)
    negative_qty = (df['Quantity'] < 0).sum()
    print(f"Negative quantities: {negative_qty} (should be 0)")
    
    # Check actions match quantities
    print("\nAction validation:")
    print(f"All quantities positive: {(df['Quantity'] > 0).all()}")
    print(f"All fees are 0: {(df['Fees'] == 0).all()}")
    print(f"All counterparties are FRGM: {(df['Counterparty'] == 'FRGM').all()}")
    
    # Export to CSV for detailed inspection
    output_file = "data/output/test_active_trade_processing_output.csv"
    df.to_csv(output_file, index=False)
    print(f"\nFull output saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    print("Testing ACTIVE Trade Processing System")
    print("=" * 80)
    
    # First inspect the raw files
    inspect_csv_files()
    
    # Then run the processing
    df = run_trade_processing()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80) 