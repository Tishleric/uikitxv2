#!/usr/bin/env python3
"""
ACTIVE Script: Step Through TYU5 Calculations

This script runs data through TYU5 with pauses after each calculation step,
allowing inspection of intermediate results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def pause_and_show(step_name, data=None):
    """Pause execution and show data."""
    print("\n" + "="*80)
    print(f"STEP: {step_name}")
    print("="*80)
    if data is not None:
        print(data)
    print("\nPress Enter to continue...")
    input()

def main():
    print("STEP-BY-STEP TYU5 CALCULATION WALKTHROUGH")
    print("="*80)
    
    # Step 1: Initialize and get market prices
    print("\n1. INITIALIZING TYU5 ADAPTER")
    from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
    adapter = TYU5Adapter()
    
    market_prices_df = adapter.get_market_prices()
    pause_and_show("Market Prices DataFrame", 
                   f"Shape: {market_prices_df.shape}\n"
                   f"Columns: {list(market_prices_df.columns)}\n\n"
                   f"First 5 rows:\n{market_prices_df.head().to_string()}")
    
    # Step 2: Get trades
    print("\n2. GETTING TRADES FROM DATABASE")
    trades_df = adapter.get_trades_for_calculation()
    pause_and_show("Trades DataFrame",
                   f"Shape: {trades_df.shape}\n"
                   f"Columns: {list(trades_df.columns)}\n\n"
                   f"First 5 trades:\n{trades_df.head().to_string()}")
    
    # Step 3: Initialize TYU5 components
    print("\n3. INITIALIZING TYU5 COMPONENTS")
    from lib.trading.pnl.tyu5_pnl.core.trade_processor import TradeProcessor
    from lib.trading.pnl.tyu5_pnl.core.position_calculator import PositionCalculator
    
    tp = TradeProcessor()
    
    # Step 4: Process trades
    print("\n4. PROCESSING TRADES (FIFO)")
    if not trades_df.empty:
        # Convert trades to TYU5 format
        trades_list = trades_df.to_dict('records')
        tp.process_trades(trades_list)
        
        pause_and_show("Trade Processing Results",
                       f"Positions by symbol: {list(tp.positions.keys())}\n"
                       f"Number of lots: {sum(len(lots) for lots in tp.lot_positions.values())}\n"
                       f"Trades processed: {len(tp.trades)}")
        
        # Show detailed position info
        print("\nDetailed positions:")
        for symbol, pos_list in tp.positions.items():
            total_qty = sum(p['remaining'] for p in pos_list)
            print(f"  {symbol}: {total_qty} contracts in {len(pos_list)} lots")
    
    # Step 5: Initialize PositionCalculator
    print("\n5. INITIALIZING POSITION CALCULATOR")
    pc = PositionCalculator(tp.positions, tp.lot_positions)
    
    # Step 6: Update prices
    print("\n6. UPDATING PRICES")
    pc.update_prices(market_prices_df)
    
    pause_and_show("Price Update Results",
                   f"Current prices stored: {len(pc.current_prices)}\n"
                   f"Prior close prices stored: {len(pc.prior_close_prices)}\n\n"
                   f"Sample prices:\n" +
                   "\n".join([f"  {sym}: Flash_Close={price}" 
                             for sym, price in list(pc.current_prices.items())[:5]]))
    
    # Step 7: Calculate positions
    print("\n7. CALCULATING POSITIONS AND P&L")
    positions_df = pc.calculate_positions()
    
    pause_and_show("Positions Calculation Results",
                   f"Shape: {positions_df.shape}\n"
                   f"Columns: {list(positions_df.columns)}\n\n"
                   f"First 5 positions:\n{positions_df.head().to_string()}")
    
    # Step 8: Show P&L summary
    if not positions_df.empty:
        print("\n8. P&L SUMMARY")
        total_unrealized = positions_df['Unrealized'].sum()
        total_quantity = positions_df['Quantity'].sum()
        
        summary_text = f"""
Total Positions: {len(positions_df)}
Total Quantity: {total_quantity}
Total Unrealized P&L: ${total_unrealized:,.2f}

By Asset Type:
"""
        # Group by futures vs options
        futures_mask = ~positions_df['Symbol'].str.contains(' ')
        futures_pnl = positions_df[futures_mask]['Unrealized'].sum()
        options_pnl = positions_df[~futures_mask]['Unrealized'].sum()
        
        summary_text += f"  Futures P&L: ${futures_pnl:,.2f}\n"
        summary_text += f"  Options P&L: ${options_pnl:,.2f}\n"
        
        pause_and_show("P&L Summary", summary_text)
    
    # Step 9: Show what would be exported
    print("\n9. EXPORT PREVIEW")
    print("TYU5 would export the following sheets to Excel:")
    print("  - Positions: Current positions with P&L")
    print("  - Trades: All processed trades") 
    print("  - Lot Positions: Individual lot details")
    print("  - Summary: P&L summary by symbol")
    
    # Optional: Actually run full TYU5 calculation
    response = input("\nWould you like to run the full TYU5 calculation and export? (y/n): ")
    if response.lower() == 'y':
        print("\nRunning full TYU5 calculation...")
        from lib.trading.pnl_integration.tyu5_service import TYU5Service
        service = TYU5Service()
        result = service.calculate_pnl()
        print(f"Calculation complete. Results: {result}")
    
    print("\n" + "="*80)
    print("WALKTHROUGH COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main() 