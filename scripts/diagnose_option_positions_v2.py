"""
Extended diagnostic to find where 206 and 226 come from.
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# First, let's search for these specific numbers in the data
print("=== Searching for 206 and 226 in Trade Data ===")

# Load all trade files
trade_files = [
    'trades_20250721.csv', 'trades_20250722.csv', 'trades_20250723.csv',
    'trades_20250724.csv', 'trades_20250725.csv', 'trades_20250728.csv',
    'trades_20250729.csv', 'trades_20250730.csv', 'trades_20250731.csv',
    'trades_20250801.csv'
]

cumulative_totals = {}
daily_counts = {}

for file in trade_files:
    try:
        df = pd.read_csv(f'data/input/trade_ledger/{file}')
        date = file.replace('trades_', '').replace('.csv', '')
        
        # Count all trades by symbol
        for _, row in df.iterrows():
            symbol = row['instrumentName']
            if symbol not in cumulative_totals:
                cumulative_totals[symbol] = {'B': 0, 'S': 0, 'trades': 0}
            
            cumulative_totals[symbol][row['buySell']] += row['quantity']
            cumulative_totals[symbol]['trades'] += 1
            
            # Track daily
            if date not in daily_counts:
                daily_counts[date] = {}
            if symbol not in daily_counts[date]:
                daily_counts[date][symbol] = {'B': 0, 'S': 0}
            daily_counts[date][symbol][row['buySell']] += row['quantity']
            
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Check for any cumulative that equals 206 or 226
print("\n=== Looking for 206 or 226 in Cumulative Quantities ===")

for symbol, data in cumulative_totals.items():
    total_b = data['B']
    total_s = data['S']
    net = total_b - total_s
    closed = min(total_b, total_s)
    
    # Check if any value is 206 or 226
    values = [total_b, total_s, net, closed, data['trades']]
    if 206 in values or 226 in values:
        print(f"\nFound match for {symbol}:")
        print(f"  Total Buy: {total_b}")
        print(f"  Total Sell: {total_s}")
        print(f"  Net: {net}")
        print(f"  Expected Closed: {closed}")
        print(f"  Trade Count: {data['trades']}")

# Check running totals
print("\n=== Checking Running Totals for TYU5 ===")
running_total = {'B': 0, 'S': 0}
for date in sorted(daily_counts.keys()):
    if 'XCMEFFDPSX20250919U0ZN' in daily_counts[date]:
        day_data = daily_counts[date]['XCMEFFDPSX20250919U0ZN']
        running_total['B'] += day_data.get('B', 0)
        running_total['S'] += day_data.get('S', 0)
        net = running_total['B'] - running_total['S']
        closed = min(running_total['B'], running_total['S'])
        
        if closed == 206 or closed == 226 or abs(net) == 206 or abs(net) == 226:
            print(f"\n{date}: MATCH FOUND")
            print(f"  Cumulative Buy: {running_total['B']}")
            print(f"  Cumulative Sell: {running_total['S']}")
            print(f"  Net: {net}")
            print(f"  Closed: {closed}")

# Now let's check if these numbers come from the FIFO/LIFO engine
print("\n=== Theoretical FIFO/LIFO Analysis ===")

# Simulate what the engine might be doing
print("\nFor TYWQ25C1 112.5:")
print("  Buys: 10 + 100 + 50 = 160")
print("  Sells: 50 + 30 = 80")
print("  Expected closed: 80")
print("  Showing: 206")
print("  Difference: 206 - 80 = 126")

print("\nFor TYWQ25C1 112.75:")
print("  Buys: 100")
print("  Sells: 20")
print("  Expected closed: 20")
print("  Showing: 226")
print("  Difference: 226 - 20 = 206")

print("\n=== Pattern Analysis ===")
print("Notice: 206 appears in both cases")
print("226 - 20 = 206")
print("206 - 80 = 126")
print("\nPossible explanations:")
print("1. 206 might be a cumulative from somewhere else being added")
print("2. The numbers might be related to TYU5 futures closed positions")
print("3. There might be cross-contamination between symbols")

# Check TYU5 closed positions up to July 31
print("\n=== TYU5 Closed Positions Through July 31 ===")
tyu5_running = {'B': 0, 'S': 0}
for date in sorted(daily_counts.keys()):
    if date > '20250731':
        break
    if 'XCMEFFDPSX20250919U0ZN' in daily_counts[date]:
        day_data = daily_counts[date]['XCMEFFDPSX20250919U0ZN']
        tyu5_running['B'] += day_data.get('B', 0)
        tyu5_running['S'] += day_data.get('S', 0)

tyu5_closed_jul31 = min(tyu5_running['B'], tyu5_running['S'])
print(f"TYU5 closed through July 31: {tyu5_closed_jul31}")

# Add August 1 TYU5 trades
if 'XCMEFFDPSX20250919U0ZN' in daily_counts.get('20250801', {}):
    aug1_data = daily_counts['20250801']['XCMEFFDPSX20250919U0ZN']
    tyu5_running['B'] += aug1_data.get('B', 0)
    tyu5_running['S'] += aug1_data.get('S', 0)

tyu5_closed_aug1 = min(tyu5_running['B'], tyu5_running['S'])
print(f"TYU5 closed through August 1: {tyu5_closed_aug1}")
print(f"TYU5 closed on August 1: {tyu5_closed_aug1 - tyu5_closed_jul31}")

# Check if 206 or 226 relate to TYU5
if tyu5_closed_aug1 - tyu5_closed_jul31 == 206:
    print("\n*** FOUND IT: 206 is the TYU5 futures closed on August 1! ***")
if tyu5_closed_aug1 - tyu5_closed_jul31 == 226:
    print("\n*** FOUND IT: 226 is the TYU5 futures closed on August 1! ***")