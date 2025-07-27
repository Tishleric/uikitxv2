"""
Quick debug script to compare our translated symbols with price file symbols
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from lib.trading.market_prices.rosetta_stone import RosettaStone

# Load trades and translate
trades_df = pd.read_csv("data/input/trade_ledger/trades_20250714.csv")
translator = RosettaStone()

print("Our translated symbols:")
translated_symbols = set()
for idx, row in trades_df.iterrows():
    symbol = translator.translate(row['instrumentName'], 'actanttrades', 'bloomberg')
    if symbol:
        translated_symbols.add(symbol)
        
for symbol in sorted(translated_symbols):
    print(f"  {symbol}")

# Load price file symbols
prices_df = pd.read_csv("data/input/market_prices/options/Options_20250714_1600.csv")
price_symbols = set(prices_df['SYMBOL'].unique())

print(f"\nPrice file has {len(price_symbols)} unique symbols")

# Find matching symbols
matching = translated_symbols & price_symbols
print(f"\nMatching symbols: {len(matching)}")
for symbol in sorted(matching):
    print(f"  {symbol}")

# Show unmatched symbols
unmatched = translated_symbols - price_symbols
if unmatched:
    print(f"\nOur symbols NOT in price file: {len(unmatched)}")
    for symbol in sorted(unmatched):
        print(f"  {symbol}")
        # Find closest match
        parts = symbol.split()
        if len(parts) >= 2:
            prefix = parts[0]
            strike = parts[1]
            similar = [ps for ps in price_symbols if ps.startswith(prefix) and strike in ps]
            if similar:
                print(f"    Closest match: {similar[0]}")
                
# Check if specific expected symbols exist
print("\nChecking specific symbols:")
test_symbols = [
    "VBYN25C2 110.750 Comdty",
    "VBYN25P2 110.750 Comdty",
    "3MN5P 110.750 Comdty"
]
for symbol in test_symbols:
    exists = symbol in price_symbols
    print(f"  {symbol}: {'FOUND' if exists else 'NOT FOUND'}") 