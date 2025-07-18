#!/usr/bin/env python
"""Detailed test of market price lookup for TYU5 symbols."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter


def test_price_lookup():
    """Test market price lookup in detail."""
    
    print("=" * 80)
    print("DETAILED PRICE LOOKUP TEST")
    print("=" * 80)
    
    adapter = TYU5Adapter()
    
    # Test specific symbols
    test_symbols = [
        "VY3N5 P 109.500",  # TYU5 format
        "VY3N5 P 110.000",
        "VY3N5 P 110.250",
        "WY4N5 P 109.750",
        "WY4N5 P 110.500",
    ]
    
    print("\n1. Testing get_market_prices_for_symbols method")
    print("-" * 60)
    
    for symbol in test_symbols:
        print(f"\nTesting: {symbol}")
        
        # Get prices using adapter method
        prices_df = adapter.get_market_prices_for_symbols([symbol])
        
        if not prices_df.empty:
            print(f"  ✓ Found price: {prices_df.iloc[0]['Current_Price']}")
        else:
            print(f"  ✗ No price found")
            
            # Debug the lookup process
            parts = symbol.split()
            if len(parts) >= 3:
                cme_base = parts[0]
                option_type = parts[1]
                strike = parts[2]
                
                # Show the conversion
                bloomberg_base = adapter._convert_cme_to_bloomberg_base(cme_base)
                print(f"  CME base: {cme_base}")
                print(f"  Bloomberg base (raw): {bloomberg_base}")
                
                # Show what the final lookup symbol would be
                # Apply the fix logic from get_market_prices_for_symbols
                if bloomberg_base.endswith('P'):
                    bloomberg_base_fixed = bloomberg_base[:-1] + option_type
                elif '3M' in bloomberg_base:
                    bloomberg_base_fixed = bloomberg_base[:-1] + option_type
                else:
                    if len(bloomberg_base) >= 8:
                        prefix = bloomberg_base[:3]
                        month = bloomberg_base[3]
                        year = bloomberg_base[4:6]
                        week = bloomberg_base[7]
                        bloomberg_base_fixed = f"{prefix}{month}{year}{option_type}{week}"
                    else:
                        bloomberg_base_fixed = bloomberg_base
                
                bloomberg_symbol = f"{bloomberg_base_fixed} {strike} Comdty"
                print(f"  Final lookup symbol: {bloomberg_symbol}")
                
                # Check if this symbol exists in the database
                market_db = Path("data/output/market_prices/market_prices.db")
                if market_db.exists():
                    conn = sqlite3.connect(str(market_db))
                    query = "SELECT symbol, current_price FROM options_prices WHERE symbol = ?"
                    result = pd.read_sql_query(query, conn, params=[bloomberg_symbol])
                    
                    if not result.empty:
                        print(f"  ✓ Symbol exists in DB: {result.iloc[0]['current_price']}")
                    else:
                        print(f"  ✗ Symbol NOT in DB")
                        
                        # Try to find similar symbols
                        similar_query = "SELECT symbol FROM options_prices WHERE symbol LIKE ? LIMIT 5"
                        similar_base = bloomberg_base_fixed.split()[0] if ' ' in bloomberg_base_fixed else bloomberg_base_fixed[:3]
                        similar_result = pd.read_sql_query(similar_query, conn, params=[f"{similar_base}%"])
                        if not similar_result.empty:
                            print(f"  Similar symbols in DB:")
                            for s in similar_result['symbol']:
                                print(f"    - {s}")
                    
                    conn.close()


if __name__ == "__main__":
    test_price_lookup() 