"""
Check which trades failed symbol translation and why
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from lib.trading.market_prices.rosetta_stone import RosettaStone

# Load trades
trades_df = pd.read_csv("data/input/trade_ledger/trades_20250714.csv")
translator = RosettaStone()

print("Analyzing symbol translation failures...")
print("=" * 80)

failed_count = 0
for idx, row in trades_df.iterrows():
    symbol = translator.translate(row['instrumentName'], 'actanttrades', 'bloomberg')
    if symbol is None:
        failed_count += 1
        print(f"\nFailed to translate: {row['instrumentName']}")
        print(f"  Trade ID: {row['tradeId']}")
        print(f"  Price: {row['price']}")
        
        # Try to diagnose the issue
        actant_symbol = row['instrumentName']
        if not actant_symbol.startswith('XCME'):
            print("  Issue: Does not start with XCME")
        elif 'XCMEOCADPS' not in actant_symbol and 'XCMEOPADPS' not in actant_symbol:
            print("  Issue: Invalid option type code")
        else:
            # Extract parts manually
            import re
            pattern = r'XCME(OCAD|OPAD)PS(\d{8})N0([A-Z]{2})(\d+)/(\d+(?:\.\d+)?)'
            match = re.match(pattern, actant_symbol)
            if not match:
                print("  Issue: Does not match expected pattern")
            else:
                parts = match.groups()
                print(f"  Parsed parts: {parts}")
                series = parts[2]
                if series not in ['VY', 'TJ', 'WY', 'TH', 'ZN']:
                    print(f"  Issue: Unknown series code: {series}")

print(f"\nTotal failed translations: {failed_count}/{len(trades_df)}")

# Also check for futures or other non-option symbols
print("\n" + "=" * 80)
print("Checking for non-option instruments...")

for idx, row in trades_df.iterrows():
    symbol = row['instrumentName']
    if not (symbol.startswith('XCMEOCAD') or symbol.startswith('XCMEOPAD')):
        print(f"Non-option symbol: {symbol}") 