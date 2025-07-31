"""
Final Trade Converter - Manual Parsing

This script performs a direct conversion of the net position streaming CSV 
into a single, clean trade ledger file.

Version 4 uses a manual, line-by-line parsing method to bypass a 
suspected file encoding or invisible character issue that causes
standard parsers to drop the last row.

It will:
1. Manually read and parse all 120 rows of trade data.
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

def convert_source_data_final():
    """
    Reads, transforms, and saves the trade data to a single output file,
    using manual parsing to ensure all rows are processed correctly.
    """
    if not SOURCE_CSV.exists():
        print(f"Error: Source file not found at {SOURCE_CSV}")
        return

    print(f"Manually parsing source file: {SOURCE_CSV}")
    
    with open(SOURCE_CSV, 'r') as f:
        lines = f.readlines()

    header = lines[0].strip().split(',')
    data = [line.strip().split(',') for line in lines[1:] if line.strip()]
    
    df = pd.DataFrame(data, columns=header)
    print(f"Successfully loaded {len(df)} rows from source.")

    # --- Data Transformation ---
    print("Transforming data...")

    # 1. Combine Date and Time into a single datetime object
    df['marketTradeTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # 2. Handle Timezone Conversion (EST -> CDT)
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_localize('America/New_York', ambiguous='infer')
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_convert('America/Chicago')
    df['marketTradeTime'] = df['marketTradeTime'].dt.tz_localize(None)

    # 3. Create 'instrumentName'
    df['instrumentName'] = 'XCMEFFDPSX20250919U0ZN'

    # 4. Create 'buySell' from 'SideName'
    df['buySell'] = df['SideName'].str[0]

    # 5. Rename columns and ensure correct data types
    df.rename(columns={'Quantity': 'quantity', 'Price': 'price'}, inplace=True)
    df['quantity'] = df['quantity'].astype(float)
    df['price'] = df['price'].astype(float)

    # 6. Generate 'tradeId'
    df['tradeId'] = range(1, len(df) + 1)

    # --- Select Final Columns and Save ---
    
    final_columns = [
        'tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price'
    ]
    final_df = df[final_columns]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving {len(final_df)} converted trades to: {OUTPUT_CSV}")
    final_df.to_csv(OUTPUT_CSV, index=False, date_format='%Y-%m-%d %H:%M:%S.%f')

    print("\nConversion complete.")

if __name__ == "__main__":
    convert_source_data_final()
