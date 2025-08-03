"""
Script to merge broker trades with existing trade ledger for August 1st.
This creates a complete trade ledger with all trades.
"""

import pandas as pd
from datetime import datetime

def clean_broker_trades(broker_csv_path):
    """Clean the converted broker trades."""
    df = pd.read_csv(broker_csv_path)
    
    # Fix the buySell column - remove extra quotes
    df['buySell'] = df['buySell'].str.strip().str.strip('"').str.strip()
    
    # Remove any remaining quotes from instrument names
    df['instrumentName'] = df['instrumentName'].str.strip().str.strip('"')
    
    return df

def merge_trade_data():
    """Merge broker trades with existing trade ledger."""
    # Load existing trade ledger
    ledger_df = pd.read_csv('data/input/trade_ledger/trades_20250801.csv')
    
    # Load and clean broker trades
    broker_df = clean_broker_trades('data/output/broker_trades_converted_20250801.csv')
    
    # Filter ledger for non-August 1st trades (to preserve July 31st late trades)
    ledger_df['trade_date'] = pd.to_datetime(ledger_df['marketTradeTime']).dt.date
    non_aug1_trades = ledger_df[ledger_df['trade_date'] != pd.to_datetime('2025-08-01').date()]
    
    print(f"Existing ledger has {len(ledger_df)} trades")
    print(f"  - Non-Aug 1 trades: {len(non_aug1_trades)}")
    print(f"  - Aug 1 trades: {len(ledger_df) - len(non_aug1_trades)}")
    print(f"Broker data has {len(broker_df)} Aug 1 trades")
    
    # Combine: keep non-Aug 1 trades from ledger, use broker data for Aug 1
    # First, renumber the tradeIds to avoid conflicts
    max_existing_id = ledger_df['tradeId'].max()
    broker_df['tradeId'] = range(max_existing_id + 1, max_existing_id + 1 + len(broker_df))
    
    # Combine the dataframes
    merged_df = pd.concat([non_aug1_trades[['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price']], 
                          broker_df], ignore_index=True)
    
    # Sort by time
    merged_df = merged_df.sort_values('marketTradeTime')
    merged_df = merged_df.reset_index(drop=True)
    
    print(f"\nMerged trade ledger has {len(merged_df)} total trades")
    
    # Save the merged file
    output_path = 'data/input/trade_ledger/trades_20250801_complete.csv'
    merged_df.to_csv(output_path, index=False)
    print(f"Saved complete trade ledger to: {output_path}")
    
    # Show summary by symbol
    print("\n=== Trade Summary by Symbol ===")
    symbol_counts = merged_df['instrumentName'].value_counts()
    for symbol, count in symbol_counts.items():
        print(f"{symbol}: {count} trades")
    
    # Calculate net positions
    print("\n=== Net Position Changes ===")
    for symbol in merged_df['instrumentName'].unique():
        symbol_trades = merged_df[merged_df['instrumentName'] == symbol]
        buys = symbol_trades[symbol_trades['buySell'] == 'B']['quantity'].sum()
        sells = symbol_trades[symbol_trades['buySell'] == 'S']['quantity'].sum()
        net = buys - sells
        print(f"{symbol}: Buys={buys}, Sells={sells}, Net={net:+.0f}")

if __name__ == "__main__":
    merge_trade_data()