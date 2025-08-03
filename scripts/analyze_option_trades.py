"""
Analyze option trades to understand closed position discrepancy.
"""

import pandas as pd

# Load trades
df = pd.read_csv('data/input/trade_ledger/trades_20250801.csv')

# Find all option trades
option_trades = df[df['instrumentName'].str.contains('XCMEO[CP]ADPS', regex=True)]

print("=== Option Trades Analysis ===")
print(f"Total option trades: {len(option_trades)}")
print("\nBreakdown by symbol:")

# Group by instrument and show buys/sells
for instrument in option_trades['instrumentName'].unique():
    trades = option_trades[option_trades['instrumentName'] == instrument]
    buys = trades[trades['buySell'] == 'B']
    sells = trades[trades['buySell'] == 'S']
    
    total_buy_qty = buys['quantity'].sum()
    total_sell_qty = sells['quantity'].sum()
    net = total_buy_qty - total_sell_qty
    
    print(f"\n{instrument}:")
    print(f"  Buys: {len(buys)} trades, {total_buy_qty} total quantity")
    print(f"  Sells: {len(sells)} trades, {total_sell_qty} total quantity")
    print(f"  Net position: {net}")
    print(f"  Expected closed: {min(total_buy_qty, total_sell_qty)}")

# Now let's trace where 206 and 226 might come from
print("\n=== Investigating the 206 and 226 numbers ===")

# Check for 112.5 strike
trades_112_5 = option_trades[option_trades['instrumentName'].str.contains('112.5')]
print(f"\nAll trades for 112.5 strike:")
for _, trade in trades_112_5.iterrows():
    print(f"  {trade['buySell']} {trade['quantity']} @ {trade['price']}")

# Check for 112.75 strike  
trades_112_75 = option_trades[option_trades['instrumentName'].str.contains('112.75')]
print(f"\nAll trades for 112.75 strike:")
for _, trade in trades_112_75.iterrows():
    print(f"  {trade['buySell']} {trade['quantity']} @ {trade['price']}")

# Let's also check if there are trades from other days
print("\n=== Checking trades from previous dates ===")
all_files = ['trades_20250729.csv', 'trades_20250730.csv', 'trades_20250731.csv']
for file in all_files:
    try:
        df = pd.read_csv(f'data/input/trade_ledger/{file}')
        option_trades = df[df['instrumentName'].str.contains('XCMEO[CP]ADPS', regex=True)]
        if len(option_trades) > 0:
            print(f"\n{file}: Found {len(option_trades)} option trades")
            for instrument in option_trades['instrumentName'].unique():
                trades = option_trades[option_trades['instrumentName'] == instrument]
                print(f"  {instrument}: {len(trades)} trades")
    except:
        pass