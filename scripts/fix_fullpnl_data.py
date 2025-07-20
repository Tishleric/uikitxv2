#!/usr/bin/env python3
"""
Manually update Greeks and market prices in FULLPNL for debugging.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.fullpnl.builder import FULLPNLBuilder

def main():
    """Update Greeks and market prices."""
    print("Fixing FULLPNL data...")
    print("="*60)
    
    # Initialize builder
    builder = FULLPNLBuilder()
    
    # Update Greeks
    print("\n1. Updating Greeks...")
    greek_results = builder.update_greeks()
    print(f"   Greek updates: {greek_results}")
    
    # Update market prices
    print("\n2. Updating market prices...")
    price_results = builder.update_market_prices()
    print(f"   Price updates: {price_results}")
    
    # Check results
    print("\n3. Checking TYU5 data...")
    import sqlite3
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, bid, ask, price, px_last, px_settle, 
               delta_f, gamma_f, gamma_y, vega_f, vega_y
        FROM FULLPNL
        WHERE symbol = 'TYU5 Comdty'
    """)
    
    row = cursor.fetchone()
    if row:
        cols = ['symbol', 'bid', 'ask', 'price', 'px_last', 'px_settle', 
                'delta_f', 'gamma_f', 'gamma_y', 'vega_f', 'vega_y']
        for i, col in enumerate(cols):
            print(f"   {col}: {row[i]}")
    
    print("\nDone!")
    conn.close()

if __name__ == "__main__":
    main() 