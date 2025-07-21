#!/usr/bin/env python3
"""Test TYU5 with debug mode enabled to verify fixes."""

import pandas as pd
from datetime import datetime
from lib.trading.pnl_integration.tyu5_runner import TYU5Runner
from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter

def test_tyu5_debug():
    """Test TYU5 with debug logging enabled."""
    print("Testing TYU5 with debug mode...")
    
    # Use the trade ledger adapter to get properly formatted data
    adapter = TradeLedgerAdapter()
    data_dict = adapter.prepare_tyu5_data()
    trades_df = data_dict['Trades_Input']
    market_prices_df = data_dict.get('Market_Prices')
    
    # Run TYU5 with debug mode enabled
    runner = TYU5Runner()
    result = runner.run_with_capture(
        trades_df=trades_df,
        market_prices_df=market_prices_df,
        debug=True  # Enable debug logging
    )
    
    # Check results
    if 'positions_df' in result:
        positions = result['positions_df']
        print(f"\nProcessed {len(positions)} positions")
        
        # Check for attribution errors
        if 'attribution_error' in positions.columns:
            errors = positions[positions['attribution_error'].notna()]
            if not errors.empty:
                print("\nAttribution errors found:")
                for idx, row in errors.iterrows():
                    print(f"  {row['Symbol']}: {row['attribution_error']}")
            else:
                print("\n✓ No attribution errors - expiration calendar fix worked!")
                
        # Check for awaiting data
        if 'Unrealized_PNL' in positions.columns:
            awaiting = positions[positions['Unrealized_PNL'] == 'awaiting data']
            if not awaiting.empty:
                print(f"\nPositions awaiting price data:")
                for idx, row in awaiting.iterrows():
                    print(f"  {row['Symbol']}: Missing current price")
                    
    print(f"\nExcel output: {runner.output_file}")
    print("Check the 'Debug_Logs' sheet for detailed calculation trace")
    
if __name__ == "__main__":
    test_tyu5_debug() 