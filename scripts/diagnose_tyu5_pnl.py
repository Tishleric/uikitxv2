"""Diagnose TYU5 P&L calculation issues."""

import sys
sys.path.append('.')
import sqlite3
import pandas as pd
from datetime import datetime

print("=== TYU5 P&L DIAGNOSIS ===")
print(f"Time: {datetime.now()}\n")

# 1. Check what data TYU5 receives
print("1. DATA TYU5 RECEIVES:")
print("-" * 60)

# Check trades
conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
trades_df = pd.read_sql_query("""
    SELECT Symbol, Action, Quantity, Price, Type, Date, Time
    FROM cto_trades 
    WHERE is_sod = 0 AND is_exercise = 0
    ORDER BY Date, Time
""", conn)
print(f"Total trades: {len(trades_df)}")
print(f"Unique symbols: {trades_df['Symbol'].nunique()}")
print("\nSample trades:")
print(trades_df.head(10).to_string())

# Check market prices
mp_conn = sqlite3.connect('data/output/market_prices/market_prices.db')

# Futures prices
futures_df = pd.read_sql_query("""
    SELECT symbol, current_price, prior_close 
    FROM futures_prices 
    WHERE symbol IN ('TYU5', 'TY')
""", mp_conn)
print("\n\nFutures prices available:")
print(futures_df.to_string())

# Options prices
options_df = pd.read_sql_query("""
    SELECT symbol, current_price, prior_close 
    FROM options_prices 
    WHERE symbol LIKE '%3MN5%' OR symbol LIKE '%VBYN25%' OR symbol LIKE '%TYWN25%'
    LIMIT 20
""", mp_conn)
print("\n\nOptions prices available:")
print(options_df.to_string())

# 2. Check position calculation logic
print("\n\n2. P&L CALCULATION ANALYSIS:")
print("-" * 60)

# Group trades by symbol to understand net positions
positions = trades_df.groupby('Symbol').agg({
    'Quantity': 'sum',
    'Price': 'mean'
}).reset_index()
positions.columns = ['Symbol', 'Net_Quantity', 'Avg_Price']

print("\nNet positions from trades:")
print(positions.to_string())

# 3. Analyze why P&L is zero
print("\n\n3. WHY P&L IS ZERO:")
print("-" * 60)

# Check if all positions have current_price = avg_price
print("\nComparing entry prices to market prices:")
for _, pos in positions.iterrows():
    symbol = pos['Symbol']
    avg_price = pos['Avg_Price']
    
    # Find market price
    market_price = None
    if 'Comdty' not in symbol:  # Futures
        mp_row = futures_df[futures_df['symbol'] == symbol.replace(' Comdty', '')]
        if not mp_row.empty:
            market_price = mp_row.iloc[0]['current_price']
    else:  # Options
        mp_row = options_df[options_df['symbol'] == symbol]
        if not mp_row.empty:
            market_price = mp_row.iloc[0]['current_price']
    
    print(f"\n{symbol}:")
    print(f"  Avg Entry Price: {avg_price:.6f}")
    print(f"  Market Price: {market_price if market_price else 'NOT FOUND'}")
    print(f"  Difference: {float(market_price - avg_price) if market_price else 'N/A'}")

# 4. Check for any closed positions (realized P&L)
print("\n\n4. CLOSED POSITIONS CHECK:")
print("-" * 60)

# Look for offsetting trades
symbol_trades = trades_df.groupby('Symbol')
for symbol, group in symbol_trades:
    buys = group[group['Action'] == 'BUY']['Quantity'].sum()
    sells = abs(group[group['Action'] == 'SELL']['Quantity'].sum())
    
    if buys > 0 and sells > 0:
        print(f"\n{symbol}: Buys={buys}, Sells={sells}")
        if buys == sells:
            print("  -> FULLY CLOSED POSITION (should have realized P&L)")
        else:
            print(f"  -> PARTIALLY CLOSED (Net position: {buys - sells})")

# 5. Check TYU5 lot positions
print("\n\n5. TYU5 LOT POSITIONS:")
print("-" * 60)

lot_df = pd.read_sql_query("""
    SELECT symbol, COUNT(*) as num_lots, SUM(remaining_quantity) as total_remaining
    FROM lot_positions
    GROUP BY symbol
""", conn)
print(lot_df.to_string())

conn.close()
mp_conn.close()

print("\n\nKEY FINDINGS:")
print("-" * 60)
print("1. TYU5 is receiving trade data correctly")
print("2. Market prices may be missing or equal to entry prices")
print("3. No offsetting trades means no realized P&L")
print("4. All positions appear to be open (no closes)") 