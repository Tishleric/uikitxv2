"""
Test the Trade Preprocessor

Tests the preprocessor with actual trade files and verifies:
1. Symbol translation
2. SOD detection
3. Expiry detection
4. File tracking (reprocessing only when changed)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pandas as pd
import time
from datetime import datetime

from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor


def display_results(df: pd.DataFrame, title: str = "Processing Results"):
    """Display processing results in a nice format."""
    print(f"\n{title}")
    print("=" * 80)
    
    # Summary stats
    print(f"Total trades: {len(df)}")
    print(f"  - Translated successfully: {df['bloomberg_symbol'].notna().sum()}")
    print(f"  - Translation errors: {(df['validation_status'] == 'SYMBOL_ERROR').sum()}")
    print(f"  - SOD positions: {df['is_sod'].sum()}")
    print(f"  - Expiries: {df['is_expiry'].sum()}")
    
    # Show some examples
    print("\nExamples of processed trades:")
    
    # Show a successful option translation
    success_options = df[(df['bloomberg_symbol'].notna()) & 
                        (df['instrumentName'].str.contains('OCA'))]
    if not success_options.empty:
        example = success_options.iloc[0]
        print(f"\nOption translation:")
        print(f"  Actant: {example['instrumentName']}")
        print(f"  Bloomberg: {example['bloomberg_symbol']}")
        print(f"  Quantity: {example['signed_quantity']}")
    
    # Show a futures translation
    success_futures = df[(df['bloomberg_symbol'].notna()) & 
                        (df['instrumentName'].str.contains('FFD'))]
    if not success_futures.empty:
        example = success_futures.iloc[0]
        print(f"\nFutures translation:")
        print(f"  Actant: {example['instrumentName']}")
        print(f"  Bloomberg: {example['bloomberg_symbol']}")
        print(f"  Quantity: {example['signed_quantity']}")
    
    # Show SOD trades
    sod_trades = df[df['is_sod'] == True]
    if not sod_trades.empty:
        print(f"\nSOD positions ({len(sod_trades)} found):")
        for _, trade in sod_trades.head(3).iterrows():
            print(f"  {trade['instrumentName']} @ {trade['marketTradeTime']}")
    
    # Show expiries
    expiry_trades = df[df['is_expiry'] == True]
    if not expiry_trades.empty:
        print(f"\nExpiries ({len(expiry_trades)} found):")
        for _, trade in expiry_trades.head(3).iterrows():
            print(f"  {trade['instrumentName']} @ price {trade['price']}")
    
    # Show errors
    errors = df[(df['validation_status'] != 'OK') & 
                (df['validation_status'] != 'SOD') & 
                (df['validation_status'] != 'EXPIRY')]
    if not errors.empty:
        print(f"\nErrors ({len(errors)} found):")
        for _, trade in errors.head(3).iterrows():
            print(f"  {trade['instrumentName']}: {trade['validation_status']}")


def test_reprocessing():
    """Test that files are only reprocessed when changed."""
    print("\n\nTesting file change detection...")
    print("-" * 80)
    
    # Create a test preprocessor
    preprocessor = TradePreprocessor("data/output/test_preprocessor")
    
    # Find a trade file
    trade_files = list(Path("data/input/trade_ledger").glob("trades_*.csv"))
    if not trade_files:
        print("No trade files found to test")
        return
    
    test_file = trade_files[0]
    print(f"Using test file: {test_file.name}")
    
    # Process once
    print("\nFirst processing...")
    result1 = preprocessor.process_trade_file(str(test_file))
    if result1 is not None:
        print(f"  Processed {len(result1)} trades")
    
    # Process again without changes
    print("\nSecond processing (no changes)...")
    result2 = preprocessor.process_trade_file(str(test_file))
    if result2 is None:
        print("  ✓ File not reprocessed (no changes detected)")
    else:
        print("  ✗ File was reprocessed unnecessarily")
    
    # Touch the file to simulate a change
    print("\nSimulating file modification...")
    test_file.touch()
    time.sleep(0.1)  # Ensure timestamp changes
    
    # Process again
    print("Third processing (after modification)...")
    result3 = preprocessor.process_trade_file(str(test_file))
    if result3 is not None:
        print(f"  ✓ File reprocessed after modification ({len(result3)} trades)")
    else:
        print("  ✗ File not reprocessed despite modification")


def main():
    """Run tests."""
    print("Trade Preprocessor Test")
    print("=" * 80)
    
    # Create preprocessor with test output directory
    output_dir = "data/output/test_preprocessor"
    preprocessor = TradePreprocessor(output_dir)
    
    # Find trade files
    trade_dir = Path("data/input/trade_ledger")
    trade_files = list(trade_dir.glob("trades_*.csv"))
    
    if not trade_files:
        print(f"No trade files found in {trade_dir}")
        return
    
    print(f"Found {len(trade_files)} trade files")
    
    # Process the most recent file
    latest_file = sorted(trade_files)[-1]
    print(f"\nProcessing: {latest_file.name}")
    
    # Process the file
    result = preprocessor.process_trade_file(str(latest_file))
    
    if result is not None:
        display_results(result)
        
        # Check output file
        output_files = list(Path(output_dir).glob("*_processed.csv"))
        if output_files:
            print(f"\n\nOutput files created:")
            for f in output_files:
                print(f"  - {f.name} ({f.stat().st_size:,} bytes)")
    else:
        print("Processing failed!")
    
    # Test reprocessing logic
    test_reprocessing()
    
    print("\n\nTest complete!")


if __name__ == "__main__":
    main() 