"""Test TYU5 adapter's ability to get market prices."""

import sys
sys.path.append('.')
from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter

print("=== TESTING TYU5 MARKET PRICE RETRIEVAL ===\n")

# Create adapter
adapter = TYU5Adapter()

# Get market prices
prices_df = adapter.get_market_prices()

print(f"Total prices retrieved: {len(prices_df)}")
print("\nFirst 10 prices:")
print(prices_df.head(10).to_string())

# Check for TYU5
print("\n\nTYU5 Futures price:")
tyu5_prices = prices_df[prices_df['Symbol'] == 'TYU5']
if not tyu5_prices.empty:
    print(tyu5_prices.to_string())
else:
    print("NOT FOUND!")

# Check what TYU5 format symbols we get
print("\n\nAll unique symbols in TYU5 format:")
for symbol in sorted(prices_df['Symbol'].unique())[:20]:
    print(f"  {symbol}") 