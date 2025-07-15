"""
Check futures price lookup
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

# Load futures price file
futures_dir = Path("data/input/market_prices/futures")
futures_files = sorted(futures_dir.glob("Futures_*.csv"))

print("Available futures price files:")
for f in futures_files[-5:]:  # Show last 5
    print(f"  {f.name}")

# Load most recent futures file
latest_futures = futures_files[-1]
print(f"\nChecking {latest_futures.name}:")
futures_df = pd.read_csv(latest_futures)
print(futures_df)

# Check if TY is in the price file
print("\nLooking for TY in futures prices:")
ty_rows = futures_df[futures_df['SYMBOL'] == 'TY']
if not ty_rows.empty:
    print(f"Found TY price: {ty_rows.iloc[0]['PX_LAST']}")
else:
    print("TY not found in futures price file")

# The issue: Futures prices use base symbols (TY) not contract-specific (TYU5)
print("\n" + "=" * 80)
print("ISSUE IDENTIFIED:")
print("- Futures price files contain base symbols: TY, TU, FV, US, RX")
print("- Our translator produces contract symbols: TYU5, TUU5, etc.")
print("- Need to strip month/year from Bloomberg symbol when looking up futures prices")

# Test the concept
test_symbols = ["TYU5 Comdty", "TUU5 Comdty", "FVU5 Comdty"]
print("\nMapping needed:")
for symbol in test_symbols:
    base = symbol.split()[0][:2]  # Extract first 2 chars (TY from TYU5)
    print(f"  {symbol} -> {base}") 