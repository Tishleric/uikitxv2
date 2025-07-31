"""
Simple Trade Converter

This script performs a direct conversion of the net position streaming CSV 
into a single, clean trade ledger file.

It will:
1. Read the raw trade data from 'net_position_streaming (4).csv'.
2. Convert timestamps from EST to CDT, preserving full precision.
3. Map columns to the required format.
4. Output a single CSV file with all trades.
"""

import pandas as pd
from pathlib import Path

# Define file paths
SOURCE_CSV = Path("data/reference/net_position_streaming (4).csv")
OUTPUT_DIR = Path("data/output")
OUTPUT_CSV = OUTPUT_DIR / "all_trades_converted.csv"

def convert_source_data():
    """
    Reads, transforms, and saves the trade data to a single output file.
    """
    if not SOURCE_CSV.exists():
        print(f"Error: Source file not found at {SOURCE_CSV}")
        return

    print(f"Reading source file: {SOURCE_CSV}")
    df = pd.read_csv(SOURCE_CSV)

    # --- Data Transformation ---
    print("Transforming data...")

    # 1. Combine Date and Time into a single datetime object
    df['marketTradeTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # 2. Handle Timezone Conversion (EST -> CDT)
    # Localize to America/New_York (EST/EDT) and convert to America/Chicago (CST/CDT)
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_localize('America/New_York', ambiguous='infer')
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_convert('America/Chicago')
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_localize(None) # Remove timezone for CSV output

    # 3. Create 'instrumentName'
    df['instrumentName'] = 'XCMEFFDPSX20250919U0ZN'

    # 4. Create 'buySell' from 'SideName'
    df['buySell'] = df['SideName'].str[0]

    # 5. Rename columns
    df.rename(columns={'Quantity': 'quantity', 'Price': 'price'}, inplace=True)

    # 6. Generate 'tradeId'
    df['tradeId'] = range(1, len(df) + 1)

    # --- Select Final Columns and Save ---
    
    # Define the exact column order required
    final_columns = [
        'tradeId',
        'instrumentName',
        'marketTradeTime',
        'buySell',
        'quantity',
        'price'
    ]
    final_df = df[final_columns]

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving converted trades to: {OUTPUT_CSV}")
    final_df.to_csv(OUTPUT_CSV, index=False, date_format='%Y-%m-%d %H:%M:%S.%f')

    print("\nConversion complete.")

if __name__ == "__main__":
    convert_source_data()
