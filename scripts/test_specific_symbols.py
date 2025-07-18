#!/usr/bin/env python
"""Test specific missing symbols."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter


def test_specific_symbols():
    """Test specific symbols that are missing prices."""
    
    print("=" * 80)
    print("SPECIFIC SYMBOL TEST")
    print("=" * 80)
    
    # Connect to market prices database
    market_db = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(market_db))
    
    # Check what VBYN25P3 symbols exist
    print("\n1. VBYN25P3 symbols in database:")
    print("-" * 60)
    
    query = """
    SELECT symbol, current_price, prior_close
    FROM options_prices
    WHERE symbol LIKE 'VBYN25P3%'
    ORDER BY symbol
    """
    
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Check what TYWN25P4 symbols exist
    print("\n\n2. TYWN25P4 symbols in database:")
    print("-" * 60)
    
    query = """
    SELECT symbol, current_price, prior_close
    FROM options_prices
    WHERE symbol LIKE 'TYWN25P4%'
    ORDER BY symbol
    """
    
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Test the adapter lookup
    print("\n\n3. Testing adapter lookup for missing symbols:")
    print("-" * 60)
    
    adapter = TYU5Adapter()
    
    # Test VY3N5 P 109.500 -> should map to VBYN25P3 109.500 Comdty
    test_cases = [
        ("VY3N5 P 109.500", "VBYN25P3 109.500 Comdty"),
        ("WY4N5 P 109.750", "TYWN25P4 109.750 Comdty"),
        ("WY4N5 P 110.500", "TYWN25P4 110.500 Comdty"),
    ]
    
    for tyu5_symbol, expected_bloomberg in test_cases:
        print(f"\nTesting: {tyu5_symbol}")
        print(f"Expected: {expected_bloomberg}")
        
        prices_df = adapter.get_market_prices_for_symbols([tyu5_symbol])
        
        if not prices_df.empty:
            print(f"  ✓ Found price: {prices_df.iloc[0]['Current_Price']}")
        else:
            print(f"  ✗ No price found - checking why...")
            
            # Check if the expected symbol exists
            query = "SELECT symbol, current_price FROM options_prices WHERE symbol = ?"
            result = pd.read_sql_query(query, conn, params=[expected_bloomberg])
            
            if not result.empty:
                print(f"  ! Symbol EXISTS in DB with price: {result.iloc[0]['current_price']}")
                print(f"  ! This indicates a mapping issue in the adapter")
            else:
                print(f"  ! Symbol NOT in DB: {expected_bloomberg}")
    
    conn.close()


if __name__ == "__main__":
    test_specific_symbols() 