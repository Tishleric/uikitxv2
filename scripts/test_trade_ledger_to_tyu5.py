#!/usr/bin/env python3
"""Test script for Trade Ledger to TYU5 Direct Adapter"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter
from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_adapter():
    """Test the trade ledger to TYU5 adapter."""
    print("=" * 80)
    print("TRADE LEDGER TO TYU5 ADAPTER TEST")
    print("=" * 80)
    
    # Create adapter
    adapter = TradeLedgerAdapter()
    
    print(f"\n1. Finding latest trade ledger...")
    
    # Prepare TYU5 data - will automatically use latest trade ledger
    tyu5_data = adapter.prepare_tyu5_data(trade_ledger_path=None, use_market_prices=True)
    
    trades_df = tyu5_data['Trades_Input']
    prices_df = tyu5_data['Market_Prices']
    
    print(f"\n2. Transformation Results:")
    print(f"   - Total trades: {len(trades_df)}")
    print(f"   - Market prices: {len(prices_df)}")
    
    if len(trades_df) > 0:
        print("\n3. Sample Trades (first 5):")
        print("-" * 80)
        for idx, row in trades_df.head(5).iterrows():
            print(f"   Trade {idx + 1}:")
            print(f"     Date/Time: {row['Date']} {row['Time']}")
            print(f"     Symbol: {row['Symbol']} ({row['Type']})")
            print(f"     Action: {row['Action']} {row['Quantity']} @ {row['Price']}")
            print(f"     Trade ID: {row['trade_id']}")
            if 'Bloomberg_Symbol' in row:
                print(f"     Bloomberg: {row['Bloomberg_Symbol']}")
            print()
            
        # Show type breakdown
        print("\n4. Trade Type Summary:")
        type_counts = trades_df['Type'].value_counts()
        for trade_type, count in type_counts.items():
            print(f"   - {trade_type}: {count}")
            
        # Show unique symbols
        print("\n5. Unique Symbols:")
        for symbol in sorted(trades_df['Symbol'].unique()):
            print(f"   - {symbol}")
            
    if len(prices_df) > 0:
        print("\n6. Market Prices (first 5):")
        print("-" * 80)
        for idx, row in prices_df.head(5).iterrows():
            print(f"   {row['Symbol']}:")
            print(f"     Current: {row.get('Current_Price', 'N/A')}")
            print(f"     Flash Close: {row.get('Flash_Close', 'N/A')}")
            print(f"     Prior Close: {row.get('Prior_Close', 'N/A')}")
            
    # Now test with TYU5 directly
    print("\n7. Testing TYU5 Integration:")
    print("-" * 80)
    
    tyu5_adapter = TYU5Adapter()
    output_file = "data/output/pnl/test_direct_tyu5.xlsx"
    
    # Run TYU5 calculation
    print(f"   Running TYU5 calculation...")
    
    try:
        # Change to TYU5 directory for calculation
        original_cwd = os.getcwd()
        tyu5_path = os.path.join(os.path.dirname(__file__), '..', 'lib', 'trading', 'pnl', 'tyu5_pnl')
        os.chdir(tyu5_path)
        
        # Add to sys.path and import
        sys.path.insert(0, '.')
        import main
        
        main.run_pnl_analysis(
            input_file=None,
            output_file=os.path.abspath(output_file),
            base_price=110.5,
            price_range=(-3, 3),
            steps=13,
            sample_data=tyu5_data
        )
        
        os.chdir(original_cwd)
        print("   [SUCCESS] TYU5 calculation completed!")
        print(f"   [SUCCESS] Output saved to: {output_file}")
        
    except Exception as e:
        os.chdir(original_cwd)
        print(f"   [ERROR] TYU5 calculation failed: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_adapter() 