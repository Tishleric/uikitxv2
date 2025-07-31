"""
Convert TT format trades to Actant trade ledger format

Purpose: Convert historical trades from TT format to Actant trade ledger format,
splitting by trading day (5pm-4pm CDT) and creating daily CSV files.
"""

import argparse
import pandas as pd
import pytz
from pathlib import Path
from datetime import datetime

def get_trading_day(timestamp):
    """
    Get the trading day for a given timestamp.
    Trading day runs from 5pm to 4pm CDT.
    A trade at 5:01pm on July 20 belongs to July 21 trading day.
    A trade at 3:59pm on July 21 belongs to July 21 trading day.
    """
    if isinstance(timestamp, str):
        dt = pd.to_datetime(timestamp)
    else:
        dt = timestamp
    
    # If time is >= 17:00 (5pm), it belongs to next day
    if dt.hour >= 17:
        trading_day = (dt + pd.Timedelta(days=1)).date()
    else:
        trading_day = dt.date()
    
    return trading_day


def convert_tt_to_ledger(input_file: str, output_dir: str):
    """Convert TT format trades to Actant ledger format"""
    
    # Load source CSV
    print(f"Loading trades from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Combine Date and Time columns and convert timezone
    df['datetime_est'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df['marketTradeTime'] = df['datetime_est'].dt.tz_localize('America/New_York').dt.tz_convert('America/Chicago')
    
    # Sort chronologically for proper tradeId assignment
    df = df.sort_values('marketTradeTime').reset_index(drop=True)
    
    # Generate sequential tradeIds
    df['tradeId'] = range(1, len(df) + 1)
    
    # Hardcode instrumentName
    df['instrumentName'] = 'XCMEFFDPSX20250919U0ZN'
    
    # Map Buy/Sell
    df['buySell'] = df['SideName'].map({'BUY': 'B', 'SELL': 'S'})
    
    # Select and rename columns
    final_df = pd.DataFrame({
        'tradeId': df['tradeId'],
        'instrumentName': df['instrumentName'],
        'marketTradeTime': df['marketTradeTime'].dt.strftime('%Y-%m-%d %H:%M:%S.%f'),
        'buySell': df['buySell'],
        'quantity': df['Quantity'],
        'price': df['Price']
    })
    
    # Assign trading day
    final_df['trading_day'] = final_df['marketTradeTime'].apply(
        lambda x: get_trading_day(pd.to_datetime(x))
    )
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Split by trading day and write files
    for trading_day, group in final_df.groupby('trading_day'):
        filename = f"trades_{trading_day.strftime('%Y%m%d')}.csv"
        filepath = output_path / filename
        
        # Drop the trading_day column before saving
        group.drop('trading_day', axis=1).to_csv(filepath, index=False)
        print(f"Created {filepath} with {len(group)} trades")
    
    print(f"\nConversion complete. Created {len(final_df.groupby('trading_day'))} daily files.")


def main():
    parser = argparse.ArgumentParser(description='Convert TT trades to Actant ledger format')
    parser.add_argument('--input-file', required=True, help='Path to TT format CSV file')
    parser.add_argument('--output-dir', required=True, help='Directory for output ledger files')
    
    args = parser.parse_args()
    
    convert_tt_to_ledger(args.input_file, args.output_dir)


if __name__ == '__main__':
    main()