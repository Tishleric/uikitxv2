#!/usr/bin/env python3
"""
ACTIVE: Calculate Flash P&L using trades_20250717.csv and Z:\\Trade_Control market prices
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
from lib.trading.market_prices.file_monitor import MarketPriceFileMonitor
from lib.trading.market_prices.storage import MarketPriceStorage
import pandas as pd
from datetime import date
import sqlite3

def main():
    print("="*80)
    print("FLASH P&L CALCULATION")
    print("Trade File: trades_20250717.csv")
    print("Market Prices: Z:\\Trade_Control")
    print("="*80)
    
    # Step 1: Process the specific trade file
    print("\n1. Processing trades_20250717.csv...")
    # Use absolute path relative to project root
    project_root = Path(__file__).parent.parent
    trade_file = project_root / "data/input/trade_ledger/trades_20250717.csv"
    
    if not trade_file.exists():
        print(f"ERROR: Trade file not found: {trade_file}")
        return
        
    # First, let's make sure market prices are loaded from Z:\Trade_Control
    print("\n2. Checking market prices database...")
    market_db = Path("data/output/market_prices/market_prices.db")
    
    # Check if database exists and has data
    if market_db.exists():
        conn = sqlite3.connect(str(market_db))
        cursor = conn.cursor()
        
        # Check futures prices
        cursor.execute("SELECT COUNT(*) FROM futures_prices WHERE Flash_Close IS NOT NULL")
        futures_count = cursor.fetchone()[0]
        
        # Check options prices  
        cursor.execute("SELECT COUNT(*) FROM options_prices WHERE Flash_Close IS NOT NULL")
        options_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Market prices in database:")
        print(f"  - Futures with Flash_Close: {futures_count}")
        print(f"  - Options with Flash_Close: {options_count}")
        
        if futures_count == 0 and options_count == 0:
            print("\nNo Flash_Close prices found. Market price processing may be needed.")
            print("The system should be watching Z:\\Trade_Control for price files.")
    else:
        print("Market prices database not found.")
        return
    
    # Process the trade file
    print("\n3. Processing trade file...")
    preprocessor = TradePreprocessor(enable_position_tracking=False)
    
    # Process the specific trade file
    preprocessor.process_trade_file(str(trade_file))
    print(f"Processed {trade_file.name}")
    
    # Step 4: Get processed trades from database
    print("\n4. Getting processed trades...")
    adapter = TYU5Adapter()
    trades_df = adapter.get_trades_for_calculation()
    
    if trades_df.empty:
        print("ERROR: No trades found after processing")
        return
    
    print(f"Found {len(trades_df)} trades")
    print("\nTrade summary:")
    print(trades_df[['Symbol', 'Action', 'Quantity', 'Price', 'Type']].to_string())
    
    # Step 5: Get market prices
    print("\n5. Fetching market prices...")
    market_prices_df = adapter.get_market_prices()
    
    if market_prices_df.empty:
        print("ERROR: No market prices found")
        return
    
    print(f"\nFound {len(market_prices_df)} market price records")
    
    # Show the prices we have
    print("\nMarket prices available:")
    for _, price in market_prices_df.iterrows():
        symbol = price['Symbol']
        current = price.get('Current_Price', 'N/A')
        flash = price.get('Flash_Close', 'N/A')
        prior = price.get('Prior_Close', 'N/A')
        print(f"  {symbol}: Current={current}, Flash={flash}, Prior={prior}")
    
    # Step 6: Run TYU5 P&L calculation
    print("\n6. Running TYU5 P&L calculations...")
    
    try:
        # Import TYU5 components
        tyu5_path = Path(__file__).parent.parent / "lib/trading/pnl/tyu5_pnl"
        sys.path.insert(0, str(tyu5_path))
        
        from core.trade_processor import TradeProcessor
        from core.position_calculator import PositionCalculator
        
        # Process trades through TYU5
        tp = TradeProcessor()
        processed_trades_df = tp.process_trades(trades_df)
        
        print(f"\nProcessed {len(processed_trades_df)} trades")
        print(f"Total Realized P&L from trades: ${processed_trades_df['Realized_PNL'].sum():,.2f}")
        
        # Calculate positions
        pc = PositionCalculator()
        pc.positions = tp.positions
        pc.position_details = tp.position_details
        pc.update_realized_pnl(processed_trades_df)
        pc.update_prices(market_prices_df)
        
        positions_df = pc.calculate_positions()
        
        # Debug: Show available columns
        print(f"\nDEBUG: Available columns in positions_df: {list(positions_df.columns)}")
        
        # Display results
        print("\n" + "="*80)
        print("FLASH P&L RESULTS")
        print("="*80)
        
        if positions_df.empty:
            print("\nNo open positions found")
            print("All trades may have been closed out")
        else:
            # Check which P&L columns we have
            has_flash = 'Unrealized_PNL_Flash' in positions_df.columns
            
            if has_flash:
                print("\n✅ Flash P&L calculations available")
                
                # Summary
                total_unrealized_flash = positions_df['Unrealized_PNL_Flash'].sum()
                total_realized = positions_df.get('Realized_PNL', 0).sum()
                total_flash_pnl = total_unrealized_flash + total_realized
                
                print(f"\n💰 FLASH P&L SUMMARY:")
                print(f"  Unrealized (Flash): ${total_unrealized_flash:,.2f}")
                print(f"  Realized:           ${total_realized:,.2f}")
                print(f"  ─────────────────────────────")
                print(f"  TOTAL FLASH P&L:    ${total_flash_pnl:,.2f}")
                
                # Also show current and close P&L for comparison
                if 'Unrealized_PNL_Current' in positions_df.columns:
                    total_unrealized_current = positions_df['Unrealized_PNL_Current'].sum()
                    total_current_pnl = total_unrealized_current + total_realized
                    print(f"\n  For comparison:")
                    print(f"  Total P&L (Current): ${total_current_pnl:,.2f}")
                
                if 'Unrealized_PNL_Close' in positions_df.columns:
                    total_unrealized_close = positions_df['Unrealized_PNL_Close'].sum()
                    total_close_pnl = total_unrealized_close + total_realized
                    print(f"  Total P&L (Close):   ${total_close_pnl:,.2f}")
            else:
                print("\n⚠️  Flash P&L columns not found - showing regular P&L")
                total_pnl = positions_df['Total_PNL'].sum()
                print(f"\nTotal P&L: ${total_pnl:,.2f}")
            
            # Position details
            print(f"\nOpen Positions ({len(positions_df)} total):")
            print("-" * 80)
            
            for _, pos in positions_df.iterrows():
                print(f"\n{pos['Symbol']} ({pos['Type']}):")
                print(f"  Net Quantity: {pos['Net_Quantity']}")
                print(f"  Avg Entry:    {pos['Avg_Entry_Price']:.6f}")
                
                if has_flash:
                    print(f"  Flash P&L:    ${pos['Unrealized_PNL_Flash']:,.2f}")
                    print(f"  Realized:     ${pos.get('Realized_PNL', 0):,.2f}")
                    total = pos['Unrealized_PNL_Flash'] + pos.get('Realized_PNL', 0)
                    print(f"  Total:        ${total:,.2f}")
                else:
                    print(f"  Total P&L:    ${pos['Total_PNL']:,.2f}")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\nReturning to user due to significant error")
        return
    
    print("\n" + "="*80)
    print("Calculation complete")

if __name__ == "__main__":
    main() 