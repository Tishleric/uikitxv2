#!/usr/bin/env python3
"""
ACTIVE Script: Trace TYU5 Data Flow

Shows what happens when market prices DataFrame is passed to TYU5.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("TRACING TYU5 DATA FLOW")
print("=" * 80)

# Step 1: Show the entry point
print("\n1. ENTRY POINT - TYU5Service.calculate_pnl()")
print("-" * 40)
print("From lib/trading/pnl_integration/tyu5_service.py:")
print("  - Gets market prices via TYU5Adapter.get_market_prices()")
print("  - Passes DataFrame to TYU5's main.run_calculation()")

# Step 2: Show main.run_calculation flow
print("\n\n2. TYU5 MAIN CALCULATION FLOW")
print("-" * 40)
print("From lib/trading/pnl/tyu5_pnl/main.py:")
print("  a) TradeProcessor processes trades (FIFO logic)")
print("  b) PositionCalculator.update_prices(market_prices_df)")
print("  c) PositionCalculator.calculate_positions()")

# Step 3: Show what update_prices does
print("\n\n3. POSITION CALCULATOR - update_prices()")
print("-" * 40)
print("From lib/trading/pnl/tyu5_pnl/core/position_calculator.py:")
print("""
def update_prices(self, market_prices_df: pd.DataFrame):
    for _, row in market_prices_df.iterrows():
        symbol = row['Symbol']
        # Stores Flash_Close as current price
        self.current_prices[symbol] = price_to_decimal(row['Flash_Close'])
        # Stores Prior_Close or falls back to Flash_Close
        self.prior_close_prices[symbol] = price_to_decimal(row['Prior_Close']) 
                                          if pd.notna(row['Prior_Close']) 
                                          else self.current_prices[symbol]
""")

# Step 4: Show how prices are used in calculations
print("\n\n4. HOW PRICES ARE USED IN P&L CALCULATION")
print("-" * 40)
print("In calculate_positions():")
print("  - Gets current price: self.current_prices.get(symbol, avg_price)")
print("  - Calculates unrealized P&L: (current_price - avg_cost) * quantity")
print("  - For options: Uses Bachelier model with current price")
print("  - Outputs DataFrame with columns:")
print("    Symbol, Quantity, Price, Current, Unrealized, Close, Delta, etc.")

# Step 5: Show the output
print("\n\n5. FINAL OUTPUT")
print("-" * 40)
print("TYU5 produces:")
print("  - positions_df: Current positions with P&L")
print("  - trades_df: All processed trades")
print("  - summary_df: P&L summary by symbol")
print("  - Exports to Excel: tyu5_pnl_all_YYYYMMDD_HHMMSS.xlsx")

# Demonstration with actual data
print("\n\n6. EXAMPLE WITH ACTUAL DATA")
print("-" * 40)
try:
    from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
    adapter = TYU5Adapter()
    df = adapter.get_market_prices()
    
    if not df.empty:
        # Show example of first few rows
        print("Market prices DataFrame (first 3 rows):")
        print(df.head(3).to_string(index=False))
        
        # Simulate what happens in update_prices
        print("\nWhat gets stored in PositionCalculator:")
        for idx, row in df.head(3).iterrows():
            print(f"  current_prices['{row['Symbol']}'] = {row['Flash_Close']}")
            print(f"  prior_close_prices['{row['Symbol']}'] = {row['Prior_Close']}")
    else:
        print("No market prices available for demonstration")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("TRACE COMPLETE") 