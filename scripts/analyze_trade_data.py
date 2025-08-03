"""
Diagnostic script to compare broker CSV with trade ledger and identify missing trades.
"""

import pandas as pd
import os
from datetime import datetime

def load_broker_data(file_path):
    """Load and parse the broker CSV file."""
    # Read with specific encoding to handle special characters
    df = pd.read_csv(file_path, encoding='latin1')
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    return df

def load_trade_ledger(file_path):
    """Load the trade ledger CSV."""
    return pd.read_csv(file_path)

def translate_broker_symbol(description, put_call, strike=None):
    """Translate broker symbol to our format."""
    # Clean up the description by removing quotes and extra spaces
    desc = description.strip().strip('"').strip()
    put_call = put_call.strip()
    
    # Futures translations
    translations = {
        "SEP 25 CBT 10YR TNOTE": "XCMEFFDPSX20250919U0ZN",
        "SEP 25 CBT 30YR TBOND": "XCMEFFDPSX20250919U0ZB"
    }
    
    # For futures
    if desc in translations:
        return translations[desc]
    
    # For options
    if put_call in ['C', 'P']:
        # Handle option translations
        if "AUG 25 CBT 10YR TNOTE WED WK1" in desc:
            # Wednesday Week 1 = XCMEOCADPS20250806Q0WY1 (for calls) or XCMEOPADPS (for puts)
            base = f"XCMEO{'C' if put_call == 'C' else 'P'}ADPS20250806Q0WY1"
            if strike and float(strike) > 0:
                return f"{base}/{float(strike)}"
            return base
        elif "AUG 25 CBT 10YR T NOTE W1 THURS OPT" in desc:
            # Thursday Week 1 = XCMEOCADPS20250807Q0HY1
            base = f"XCMEO{'C' if put_call == 'C' else 'P'}ADPS20250807Q0HY1"
            if strike and float(strike) > 0:
                return f"{base}/{float(strike)}"
            return base
    
    return desc

def parse_broker_time(exec_time_str):
    """Parse broker time format (HHMM) to datetime."""
    if pd.isna(exec_time_str):
        return None
    time_str = str(exec_time_str).strip().strip('"').strip()
    if len(time_str) == 4:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        return f"{hour:02d}:{minute:02d}:00"
    return None

def convert_broker_to_ledger_format(broker_df):
    """Convert broker format to our trade ledger format."""
    trades = []
    
    for idx, row in broker_df.iterrows():
        # Skip non-trade records
        if row['RECORD I D'] != 'T':
            continue
            
        # Extract fields
        symbol = translate_broker_symbol(row['DESCRIPTION'], row['PUT/CALL'], row['STRIKE PRICE'])
        
        # Parse time
        time_str = parse_broker_time(row['EXEC TIME'])
        if time_str:
            trade_time = f"2025-08-01 {time_str}.000"
        else:
            trade_time = "2025-08-01 00:00:00.000"
            
        trade = {
            'tradeId': f"broker_{idx}",
            'instrumentName': symbol,
            'marketTradeTime': trade_time,
            'buySell': row['B/S'],
            'quantity': float(row['QTY']),
            'price': float(row['TRADE PRICE'])
        }
        trades.append(trade)
    
    return pd.DataFrame(trades)

def compare_trade_data():
    """Main comparison function."""
    # Load data
    broker_df = load_broker_data('data/reference/DASONLY.20250801.csv')
    ledger_df = load_trade_ledger('data/input/trade_ledger/trades_20250801.csv')
    
    # Convert broker data to ledger format
    broker_trades_df = convert_broker_to_ledger_format(broker_df)
    
    # Filter for August 1st trades only in ledger
    ledger_df['trade_date'] = pd.to_datetime(ledger_df['marketTradeTime']).dt.date
    aug1_ledger = ledger_df[ledger_df['trade_date'] == pd.to_datetime('2025-08-01').date()]
    
    print("=== Trade Data Analysis ===")
    print(f"\nBroker CSV total records: {len(broker_df)}")
    print(f"Broker trade records: {len(broker_df[broker_df['RECORD I D'] == 'T'])}")
    print(f"Trade ledger total records: {len(ledger_df)}")
    print(f"Trade ledger Aug 1 records: {len(aug1_ledger)}")
    
    # Symbol analysis
    print("\n=== Symbol Distribution in Broker Data ===")
    symbol_counts = broker_df[broker_df['RECORD I D'] == 'T']['DESCRIPTION'].value_counts()
    for symbol, count in symbol_counts.items():
        print(f"{symbol}: {count} trades")
    
    # Option analysis
    option_trades = broker_df[(broker_df['RECORD I D'] == 'T') & (broker_df['PUT/CALL'].isin(['C', 'P']))]
    if len(option_trades) > 0:
        print("\n=== Option Trades in Broker Data ===")
        for idx, row in option_trades.iterrows():
            print(f"{row['DESCRIPTION']} {row['PUT/CALL']} {row['STRIKE PRICE']}: {row['B/S']} {row['QTY']} @ {row['TRADE PRICE']}")
    
    # Convert and save missing trades
    print("\n=== Converting Broker Trades ===")
    converted_df = broker_trades_df.sort_values('marketTradeTime')
    converted_df.to_csv('data/output/broker_trades_converted_20250801.csv', index=False)
    print(f"Converted {len(converted_df)} trades to ledger format")
    print("Saved to: data/output/broker_trades_converted_20250801.csv")
    
    # Show sample of converted data
    print("\n=== Sample Converted Trades ===")
    print(converted_df.head(10))

if __name__ == "__main__":
    compare_trade_data()