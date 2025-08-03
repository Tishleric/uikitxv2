"""
Diagnose if there's an accumulation bug in the daily position tracking.
"""

import pandas as pd

print("=== Checking Closed Position Values in Output ===")

# From the output, we see the progression
print("\nAugust 1st Final Daily Positions:")
print("27  2025-08-01  TYU5 Comdty  fifo  -467.0  236  ...")
print("29  2025-08-01  TYWQ25C1 112.5 Comdty  fifo  80.0  206  ...")
print("30  2025-08-01  TYWQ25C1 112.75 Comdty  fifo  80.0  226  ...")

print("\n=== Analysis ===")
print("TYU5 closed: 236")
print("TYWQ25C1 112.5 closed: 206")
print("TYWQ25C1 112.75 closed: 226")

print("\n=== Pattern Discovery ===")
print("236 - 30 = 206  (TYU5 closed minus something)")
print("206 + 20 = 226  (accumulating?)")

print("\n=== Hypothesis ===")
print("The closed positions might be getting mixed up between symbols!")
print("\nLet's check if the script is accumulating across symbols...")

# Let's trace the actual trades for August 1
print("\n=== August 1 Trade Sequence ===")

trades_aug1 = pd.read_csv('data/input/trade_ledger/trades_20250801.csv')

# Create a timeline of all trades
timeline = []
for _, row in trades_aug1.iterrows():
    timeline.append({
        'time': row['marketTradeTime'],
        'symbol': row['instrumentName'],
        'bs': row['buySell'],
        'qty': row['quantity'],
        'price': row['price']
    })

# Sort by time
timeline = sorted(timeline, key=lambda x: x['time'])

# Find when options are traded relative to futures
print("\nLooking for trades around option times...")
option_times = []
for t in timeline:
    if 'XCMEO' in t['symbol']:
        option_times.append(t['time'])
        
# Show context around each option trade
for opt_time in option_times:
    print(f"\n=== Around {opt_time} ===")
    for t in timeline:
        if abs(pd.to_datetime(t['time']) - pd.to_datetime(opt_time)).total_seconds() < 300:  # 5 min window
            symbol_short = t['symbol'].split('/')[-1] if '/' in t['symbol'] else t['symbol'][-10:]
            print(f"{t['time'][-12:]} {t['bs']} {t['qty']:3.0f} {symbol_short}")

# Check if update_daily_position might be accumulating incorrectly
print("\n=== Key Insight ===")
print("If update_daily_position is called with accumulate=True (default),")
print("and the same symbol gets updated multiple times in a day,")
print("it would add to the existing closed_position value.")
print("\nBut from the rebuild script, we see accumulate=False is used.")
print("So the issue must be elsewhere...")

# Let's check the EOD logic
print("\n=== EOD Process Analysis ===")
print("The EOD process uses INSERT OR REPLACE with COALESCE to preserve")
print("existing closed_position values. This might be the issue!")
print("\nIf daily_positions already has records (from trade processing),")
print("the EOD might be preserving incorrect values.")

# Final theory
print("\n=== Most Likely Cause ===")
print("The daily_closed_positions dictionary tracks correctly (80, 20),")
print("but when written to the database, something else is happening.")
print("\nPossible issues:")
print("1. The daily_closed_positions dict is being contaminated")
print("2. The database has stale data from a previous run") 
print("3. There's a timing issue with when positions are updated")
print("4. The PositionsAggregator is adding extra closed positions")