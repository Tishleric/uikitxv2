#!/usr/bin/env python3
"""
ACTIVE Script: Show TYU5 Market Prices DataFrame Format
This demonstrates the exact DataFrame structure TYU5 expects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime

# Example of the EXACT DataFrame format TYU5 expects
# Based on analysis of lib/trading/pnl/tyu5_pnl/core/position_calculator.py

print("=" * 80)
print("TYU5 MARKET PRICES DATAFRAME FORMAT")
print("=" * 80)

# Create example DataFrame with required columns
example_data = {
    'Symbol': [
        'TYU5',                    # Futures - CME format
        'VY2N5 C 108.750',        # Call option - CME format
        'VY2N5 P 109.500',        # Put option - CME format
        'ZN3N5 C 110.250',        # Friday weekly option
        'OZNQ5 C 111.000',        # Monthly option
    ],
    'Flash_Close': [
        119.25,      # Futures price
        0.015625,    # Option price
        0.03125,     # Option price
        0.0078125,   # Option price
        0.046875,    # Option price
    ],
    'Prior_Close': [
        119.20,      # Previous close
        0.0125,      # Previous close
        0.0375,      # Previous close
        0.00625,     # Previous close
        0.05,        # Previous close
    ]
}

# Create DataFrame
tyu5_format_df = pd.DataFrame(example_data)

print("\nRequired Columns:")
print("1. Symbol - TYU5/CME format symbols")
print("2. Flash_Close - Current market price (formerly Current_Price)")
print("3. Prior_Close - Previous day's closing price")

print("\nExample DataFrame:")
print(tyu5_format_df.to_string(index=False))

print("\nData Types:")
print(tyu5_format_df.dtypes)

# Show how to create this from raw market data
print("\n" + "=" * 80)
print("HOW TO CREATE THIS DATAFRAME")
print("=" * 80)

print("""
The TYU5Adapter.get_market_prices() method:

1. Fetches from market_prices database:
   - futures_prices table (Flash_Close column)
   - options_prices table (Flash_Close column)

2. Converts symbols:
   - Bloomberg format: "TYU5 Comdty" → TYU5 format: "TYU5"
   - Bloomberg format: "VBYN25C2 108.750 Comdty" → TYU5 format: "VY2N5 C 108.750"

3. Selects required columns:
   - 'Symbol' (converted to TYU5 format)
   - 'Flash_Close' (from PX_LAST in price files)
   - 'Prior_Close' (from PX_SETTLE in price files)
""")

# Show the automation flow
print("\n" + "=" * 80)
print("AUTOMATION FLOW")
print("=" * 80)

print("""
1. Market price files arrive in Z:\\Trade_Control:
   - futures/Futures_YYYYMMDD_HHMM.csv
   - options/Options_YYYYMMDD_HHMM.csv

2. MarketPriceFileMonitor processes files:
   - FuturesProcessor → updates Flash_Close in futures_prices table
   - OptionsProcessor → updates Flash_Close in options_prices table

3. TYU5Adapter.get_market_prices() called:
   - Queries database for all prices
   - Converts Bloomberg symbols to TYU5 format
   - Returns DataFrame with Symbol, Flash_Close, Prior_Close

4. TYU5 PositionCalculator.update_prices(df):
   - Iterates through DataFrame rows
   - Updates internal price dictionaries
   - Uses for P&L calculations
""")

# Save example to CSV
output_path = "data/output/tyu5_dataframe_format_example.csv"
tyu5_format_df.to_csv(output_path, index=False)
print(f"\nExample saved to: {output_path}")

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80) 