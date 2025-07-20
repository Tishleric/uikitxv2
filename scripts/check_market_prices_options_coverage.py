#!/usr/bin/env python3
"""
Check which options are in the market prices database and compare with spot risk symbols.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from pathlib import Path
from collections import defaultdict

from lib.trading.market_prices.spot_risk_symbol_adapter import SpotRiskSymbolAdapter

def main():
    """Analyze market prices database coverage."""
    
    print("="*60)
    print("MARKET PRICES DATABASE COVERAGE ANALYSIS")
    print("="*60)
    
    # Connect to market prices database
    db_path = Path("data/output/market_prices/market_prices.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(str(db_path))
    
    # Get all options in the database for July 17
    query = """
        SELECT DISTINCT symbol 
        FROM options_prices 
        WHERE trade_date = '2025-07-17'
        ORDER BY symbol
    """
    
    db_options = pd.read_sql_query(query, conn)
    print(f"\nOptions in database for 2025-07-17: {len(db_options)}")
    
    # Get a sample
    print("\nSample options in database:")
    for symbol in db_options['symbol'].head(10):
        print(f"  {symbol}")
    
    # Load spot risk file and translate symbols
    test_file = Path("data/input/actant_spot_risk/2025-07-18/bav_analysis_20250717_145100.csv")
    df = pd.read_csv(test_file)
    df = df.iloc[1:].reset_index(drop=True)
    
    adapter = SpotRiskSymbolAdapter()
    spot_risk_options = []
    
    for _, row in df.iterrows():
        symbol = row['Key']
        if pd.isna(symbol) or 'INVALID' in str(symbol) or symbol == 'XCME.ZN':
            continue
            
        bloomberg = adapter.translate(symbol)
        if bloomberg and ' ' in bloomberg:  # It's an option
            # Remove ' Comdty' suffix for database comparison
            db_symbol = bloomberg.replace(' Comdty', '').strip()
            spot_risk_options.append({
                'spot_risk': symbol,
                'bloomberg': db_symbol,
                'has_price': not pd.isna(row.get('BID')) or not pd.isna(row.get('ADJTHEOR'))
            })
    
    print(f"\nOptions from spot risk file: {len(spot_risk_options)}")
    
    # Convert to sets for comparison
    db_set = set(db_options['symbol'])
    spot_risk_set = set(opt['bloomberg'] for opt in spot_risk_options)
    
    # Find matches and mismatches
    matched = db_set & spot_risk_set
    in_spot_not_db = spot_risk_set - db_set
    in_db_not_spot = db_set - spot_risk_set
    
    print(f"\nComparison Results:")
    print(f"  Matched (in both): {len(matched)}")
    print(f"  In spot risk but not in DB: {len(in_spot_not_db)}")
    print(f"  In DB but not in spot risk: {len(in_db_not_spot)}")
    
    # Show unmatched from spot risk
    if in_spot_not_db:
        print(f"\nOptions from spot risk NOT in database:")
        for symbol in sorted(list(in_spot_not_db))[:20]:
            # Find the original spot risk symbol
            orig = next((opt['spot_risk'] for opt in spot_risk_options if opt['bloomberg'] == symbol), 'Unknown')
            print(f"  {orig} → {symbol}")
        if len(in_spot_not_db) > 20:
            print(f"  ... and {len(in_spot_not_db)-20} more")
    
    # Analyze patterns in unmatched symbols
    print(f"\nAnalyzing patterns in unmatched symbols:")
    patterns = defaultdict(int)
    for symbol in in_spot_not_db:
        # Extract pattern (e.g., VBYN25C3 -> VBY)
        if len(symbol) >= 3:
            base = symbol[:3]
            patterns[base] += 1
    
    for base, count in sorted(patterns.items(), key=lambda x: -x[1]):
        print(f"  {base}: {count} symbols")
    
    # Check if the matched symbols have Current_Price
    if matched:
        query = """
            SELECT symbol, Current_Price, Flash_Close, prior_close
            FROM options_prices
            WHERE trade_date = '2025-07-17' AND symbol IN ({})
            AND Current_Price IS NOT NULL
        """.format(','.join('?' for _ in matched))
        
        with_current = pd.read_sql_query(query, conn, params=list(matched))
        print(f"\nOf the {len(matched)} matched options:")
        print(f"  With Current_Price: {len(with_current)}")
        print(f"  Without Current_Price: {len(matched) - len(with_current)}")
    
    conn.close()


if __name__ == "__main__":
    main() 