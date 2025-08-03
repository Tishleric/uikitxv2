"""
Trace how closed positions accumulate during the rebuild process.
Focus on understanding where 206 and 226 come from.
"""

import pandas as pd

def analyze_option_trades():
    """Analyze the pattern of option trades."""
    # Load all trade files
    all_trades = []
    
    for day in range(21, 32):  # July 21-31
        try:
            df = pd.read_csv(f'data/input/trade_ledger/trades_202507{day:02d}.csv')
            df['file'] = f'202507{day:02d}'
            all_trades.append(df)
        except:
            pass
    
    # August 1
    df = pd.read_csv('data/input/trade_ledger/trades_20250801.csv')
    df['file'] = '20250801'
    all_trades.append(df)
    
    # Combine all
    all_df = pd.concat(all_trades, ignore_index=True)
    
    # Look for our specific options
    print("=== Searching for TYWQ25C1 options across all files ===\n")
    
    # Search for any variation of these symbols
    patterns = ['112.5', '112.75', 'TYWQ25C1', 'XCMEOCADPS20250806Q0WY1']
    
    for pattern in patterns:
        matches = all_df[all_df['instrumentName'].str.contains(pattern, na=False)]
        if len(matches) > 0:
            print(f"\nFound {len(matches)} trades containing '{pattern}':")
            for _, trade in matches.iterrows():
                print(f"  File: {trade['file']}, Symbol: {trade['instrumentName']}, "
                      f"B/S: {trade['buySell']}, Qty: {trade['quantity']}")
    
    # Now let's trace the numbers
    print("\n=== Analyzing the pattern ===")
    
    # Get just August 1st option trades
    aug1_df = all_df[all_df['file'] == '20250801']
    options_df = aug1_df[aug1_df['instrumentName'].str.contains('XCMEOCADPS20250806Q0WY1')]
    
    # Group by strike
    for strike in ['112.5', '112.75']:
        strike_trades = options_df[options_df['instrumentName'].str.contains(strike)]
        if '112.75' not in strike:  # Avoid matching 112.75 when looking for 112.5
            strike_trades = strike_trades[~strike_trades['instrumentName'].str.contains('112.75')]
        
        print(f"\n{strike} Strike Analysis:")
        
        buys = strike_trades[strike_trades['buySell'] == 'B']
        sells = strike_trades[strike_trades['buySell'] == 'S']
        
        buy_total = buys['quantity'].sum()
        sell_total = sells['quantity'].sum()
        
        print(f"  Total Buys: {buy_total} ({len(buys)} trades)")
        print(f"  Total Sells: {sell_total} ({len(sells)} trades)")
        print(f"  Expected Closed: {min(buy_total, sell_total)}")
        
        # Now look for patterns that might lead to 206 or 226
        print(f"  Buy quantities: {list(buys['quantity'].values)}")
        print(f"  Sell quantities: {list(sells['quantity'].values)}")
        
        # Check various combinations
        if strike == '112.5':
            print(f"\n  Checking for 206:")
            print(f"    80 (expected) + 126 = 206")
            print(f"    Is 126 related to other trades? Let's see...")
            
            # Check if 126 appears anywhere
            all_qtys = list(options_df['quantity'].values)
            print(f"    All option quantities: {all_qtys}")
            print(f"    Sum of all option trades: {sum(all_qtys)}")
            
        elif strike == '112.75':
            print(f"\n  Checking for 226:")
            print(f"    20 (expected) + 206 = 226")
            print(f"    Notice 206 appears again!")

    # Let's check if there's cross-contamination
    print("\n=== Checking for Cross-Contamination ===")
    
    # Total all option trades
    total_option_buys = options_df[options_df['buySell'] == 'B']['quantity'].sum()
    total_option_sells = options_df[options_df['buySell'] == 'S']['quantity'].sum()
    
    print(f"Total Option Buys: {total_option_buys}")
    print(f"Total Option Sells: {total_option_sells}")
    print(f"Total Closed (if treated as one symbol): {min(total_option_buys, total_option_sells)}")
    
    # Check specific sums
    print(f"\nInteresting sums:")
    print(f"  80 + 20 = {80 + 20} (sum of expected closed)")
    print(f"  100 + 100 + 6 = {100 + 100 + 6} = 206 (!)")
    print(f"  206 + 20 = {206 + 20} = 226 (!)")
    
    # Look at trade IDs to see if there's a pattern
    print("\n=== Trade ID Analysis ===")
    option_trades = options_df.sort_values('tradeId')
    print("Option trades by ID:")
    for _, trade in option_trades.iterrows():
        print(f"  ID: {trade['tradeId']}, Symbol: {trade['instrumentName']}, "
              f"B/S: {trade['buySell']}, Qty: {trade['quantity']}")

if __name__ == "__main__":
    analyze_option_trades()