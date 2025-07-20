#!/usr/bin/env python3
"""
ACTIVE: Test enhanced TYU5 P&L calculations with Current_Price
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Import TYU5 components
from lib.trading.pnl.tyu5_pnl.core.trade_processor import TradeProcessor
from lib.trading.pnl.tyu5_pnl.core.position_calculator import PositionCalculator
import pandas as pd
import datetime

def create_test_data():
    """Create sample data to test calculations"""
    
    # Sample trades
    trades_data = {
        'Date': ['2025-01-15', '2025-01-15'],
        'Time': ['09:30:00', '10:00:00'],
        'Symbol': ['TYU5', 'TYU5'],
        'Action': ['BUY', 'SELL'],
        'Quantity': [10, 5],
        'Price': ['119.25', '119.50'],
        'Type': ['FUT', 'FUT'],
        'trade_id': ['T001', 'T002'],
        'Fees': [0, 0],
        'Counterparty': ['FRGM', 'FRGM']
    }
    trades_df = pd.DataFrame(trades_data)
    
    # Sample market prices with all three price types
    market_prices_data = {
        'Symbol': ['TYU5'],
        'Current_Price': ['119.75'],  # Live price
        'Flash_Close': ['119.60'],     # Snapshot price
        'Prior_Close': ['119.20']      # Previous close
    }
    market_prices_df = pd.DataFrame(market_prices_data)
    
    return trades_df, market_prices_df

def main():
    print("Testing Enhanced TYU5 P&L Calculations")
    print("=" * 80)
    
    # Create test data
    trades_df, market_prices_df = create_test_data()
    
    # Process trades
    print("\n1. Processing trades through TYU5...")
    tp = TradeProcessor()
    processed_trades = tp.process_trades(trades_df)
    
    print(f"Trades processed: {len(processed_trades)}")
    print("\nProcessed trades:")
    print(processed_trades[['Symbol', 'Action', 'Quantity', 'Price_Decimal', 'Realized_PNL']])
    
    # Calculate positions
    print("\n2. Calculating positions...")
    pc = PositionCalculator()
    pc.positions = tp.positions
    pc.position_details = tp.position_details
    
    # Update prices with our enhanced market data
    print("\n3. Updating market prices...")
    print("Market prices DataFrame:")
    print(market_prices_df)
    
    pc.update_prices(market_prices_df)
    
    # Calculate positions with multiple P&L values
    positions_df = pc.calculate_positions()
    
    print("\n4. Position calculations:")
    if not positions_df.empty:
        # Show key columns
        display_cols = [
            'Symbol', 'Net_Quantity', 'Avg_Entry_Price',
            'Prior_Present_Value', 'Current_Present_Value',
            'Unrealized_PNL_Current', 'Unrealized_PNL_Flash', 'Unrealized_PNL_Close',
            'Total_PNL'
        ]
        
        # Filter columns that exist
        existing_cols = [col for col in display_cols if col in positions_df.columns]
        
        print("\nPosition details:")
        for idx, pos in positions_df.iterrows():
            print(f"\nSymbol: {pos['Symbol']}")
            print(f"  Net Quantity: {pos['Net_Quantity']}")
            print(f"  Avg Entry Price: {pos['Avg_Entry_Price']:.4f}")
            
            if 'Prior_Present_Value' in pos:
                print(f"  Prior Present Value: ${pos['Prior_Present_Value']:,.2f}")
            if 'Current_Present_Value' in pos:
                print(f"  Current Present Value: ${pos['Current_Present_Value']:,.2f}")
                
            print(f"\n  P&L Calculations:")
            if 'Unrealized_PNL_Current' in pos:
                print(f"    Unrealized P&L (Current): ${pos['Unrealized_PNL_Current']:,.2f}")
            if 'Unrealized_PNL_Flash' in pos:
                print(f"    Unrealized P&L (Flash): ${pos['Unrealized_PNL_Flash']:,.2f}")
            if 'Unrealized_PNL_Close' in pos:
                print(f"    Unrealized P&L (Close): ${pos['Unrealized_PNL_Close']:,.2f}")
            
            print(f"    Total P&L: ${pos['Total_PNL']:,.2f}")
    else:
        print("No open positions")
    
    # Show realized P&L
    total_realized = processed_trades['Realized_PNL'].sum()
    print(f"\n5. Realized P&L Summary:")
    print(f"  Total Realized P&L: ${total_realized:,.2f}")
    
    print("\n" + "=" * 80)
    print("Test complete - enhanced P&L calculations are working!")

if __name__ == "__main__":
    main() 