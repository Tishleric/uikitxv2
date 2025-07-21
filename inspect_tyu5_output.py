#!/usr/bin/env python3
"""Inspect TYU5 output data before Excel writing."""

import pandas as pd
from datetime import datetime
from lib.trading.pnl_integration.tyu5_runner import TYU5Runner
from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter

def inspect_tyu5_output():
    """Run TYU5 and inspect the data structures before Excel output."""
    print("Running TYU5 to inspect output data...")
    
    # Get data
    adapter = TradeLedgerAdapter()
    data_dict = adapter.prepare_tyu5_data()
    trades_df = data_dict['Trades_Input']
    market_prices_df = data_dict.get('Market_Prices')
    
    # Run TYU5
    runner = TYU5Runner()
    result = runner.run_with_capture(
        trades_df=trades_df,
        market_prices_df=market_prices_df,
        debug=False  # Keep debug off for cleaner output
    )
    
    print("\n" + "="*80)
    print("EXACT STATE OF DATA BEFORE EXCEL OUTPUT")
    print("="*80)
    
    # 1. Processed Trades
    print("\n1. PROCESSED TRADES DataFrame:")
    print("-"*80)
    trades = result['processed_trades_df']
    print(f"Shape: {trades.shape}")
    print(f"Columns: {trades.columns.tolist()}")
    print("\nSample data:")
    print(trades[['Trade_ID', 'Symbol', 'Action', 'Quantity', 'Realized_PNL']].head(10))
    print(f"\nTotal Realized P&L: ${trades['Realized_PNL'].sum():,.2f}")
    
    # Check for closed position tracking
    print("\nChecking for closed position tracking in trades:")
    if 'Matched_Quantity' in trades.columns:
        print("✓ Matched_Quantity column found")
        matched = trades[trades['Matched_Quantity'] > 0]
        print(f"  Trades with matches: {len(matched)}")
    else:
        print("✗ No Matched_Quantity column - closed positions not tracked in trades")
    
    # 2. Positions
    print("\n\n2. POSITIONS DataFrame:")
    print("-"*80)
    positions = result['positions_df']
    print(f"Shape: {positions.shape}")
    print(f"Columns: {positions.columns.tolist()}")
    print("\nFull positions data:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(positions)
    
    # 3. Summary
    print("\n\n3. SUMMARY DataFrame:")
    print("-"*80)
    summary = result['summary_df']
    print(summary)
    
    # 4. Risk Matrix
    print("\n\n4. RISK MATRIX DataFrame:")
    print("-"*80)
    risk = result['risk_df']
    print(f"Shape: {risk.shape}")
    print(f"Columns: {risk.columns.tolist()}")
    print("First few rows:")
    print(risk.head())
    
    # 5. Breakdown
    print("\n\n5. BREAKDOWN DataFrame:")
    print("-"*80)
    breakdown = result['breakdown_df']
    print(f"Shape: {breakdown.shape}")
    print(f"Columns: {breakdown.columns.tolist()}")
    print("\nBreakdown by label:")
    print(breakdown.groupby('Label').size())
    
    # Check internal structures for closed position info
    print("\n\n6. CHECKING FOR CLOSED POSITION TRACKING:")
    print("-"*80)
    
    # Check if match_history exists
    print("\nLooking for match history...")
    # We can't directly access internal structures from here, but we can check the trades
    
    # Look for any indication of closed positions
    sell_trades = trades[trades['Action'] == 'SELL']
    buy_trades = trades[trades['Action'] == 'BUY']
    
    print(f"SELL trades: {len(sell_trades)}")
    print(f"BUY trades: {len(buy_trades)}")
    
    # Check if any trades resulted in closed positions
    trades_with_realized = trades[trades['Realized_PNL'] != 0]
    if not trades_with_realized.empty:
        print(f"\n✓ Found {len(trades_with_realized)} trades with realized P&L:")
        for idx, trade in trades_with_realized.iterrows():
            print(f"  {trade['Symbol']}: {trade['Action']} {trade['Quantity']} @ {trade['Price_32nds']} = ${trade['Realized_PNL']:,.2f}")
    else:
        print("\n✗ No trades with realized P&L found")
    
    # Save detailed output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tyu5_inspection_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write("TYU5 OUTPUT INSPECTION\n")
        f.write("="*80 + "\n\n")
        
        f.write("1. PROCESSED TRADES:\n")
        f.write(trades.to_string() + "\n\n")
        
        f.write("2. POSITIONS:\n")
        f.write(positions.to_string() + "\n\n")
        
        f.write("3. SUMMARY:\n")
        f.write(summary.to_string() + "\n\n")
        
        f.write("4. RISK MATRIX:\n")
        f.write(risk.to_string() + "\n\n")
        
        f.write("5. BREAKDOWN:\n")
        f.write(breakdown.to_string() + "\n")
    
    print(f"\n\nDetailed output saved to: {output_file}")
    
if __name__ == "__main__":
    inspect_tyu5_output() 