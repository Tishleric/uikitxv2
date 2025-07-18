#!/usr/bin/env python
"""Debug Symbol Mapping and Market Price Lookup

This script investigates why transformed TYU5 symbols can't find market prices.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter


def debug_symbol_mapping():
    """Debug symbol mapping and market price lookup."""
    
    print("=" * 80)
    print("SYMBOL MAPPING DEBUG")
    print("=" * 80)
    
    # Initialize adapter
    adapter = TYU5Adapter()
    
    # Test specific option symbol transformations
    test_symbols = [
        "VBYN25P3 109.500 Comdty",
        "TYWN25P4 109.750 Comdty",
        "3MN5P 110.000 Comdty"
    ]
    
    print("\n1. SYMBOL TRANSFORMATION TEST")
    print("-" * 60)
    
    for bloomberg_symbol in test_symbols:
        # Extract base symbol
        parts = bloomberg_symbol.split()
        base = parts[0]
        
        # Test the mapping function
        cme_symbol = adapter._map_bloomberg_to_cme(base)
        print(f"\nBloomberg base: {base}")
        print(f"CME mapped:     {cme_symbol}")
        
        # Show what TYU5 format would be
        if "CALL" in bloomberg_symbol or "PUT" in bloomberg_symbol or base.endswith(('P', 'C')):
            # It's an option
            strike = parts[1] if len(parts) > 1 else "?"
            type_char = 'P' if 'P' in base[-2:] else 'C'
            tyu5_format = f"{cme_symbol} {type_char} {strike}"
            print(f"TYU5 format:    {tyu5_format}")
            
            # Test reverse mapping
            bloomberg_base_back = adapter._convert_cme_to_bloomberg_base(cme_symbol)
            print(f"Back to BBG:    {bloomberg_base_back}")
    
    # Check market prices database
    print("\n\n2. MARKET PRICES DATABASE CHECK")
    print("-" * 60)
    
    market_db = Path("data/output/market_prices/market_prices.db")
    if not market_db.exists():
        print(f"Market prices database not found: {market_db}")
        return
        
    conn = sqlite3.connect(str(market_db))
    
    # Check what option symbols exist in the database
    options_query = """
    SELECT DISTINCT symbol 
    FROM options_prices 
    WHERE symbol LIKE 'VBY%' OR symbol LIKE 'TYW%' OR symbol LIKE '3M%'
    ORDER BY symbol
    LIMIT 20
    """
    
    options_df = pd.read_sql_query(options_query, conn)
    print("\nOption symbols in market prices DB:")
    for symbol in options_df['symbol']:
        print(f"  - {symbol}")
    
    # Test specific lookups
    print("\n\n3. SPECIFIC SYMBOL LOOKUP TEST")
    print("-" * 60)
    
    # Try to find prices for our test symbols
    for symbol in ["VBYN25P3 109.500 Comdty", "VY3N5 P 109.500"]:
        query = """
        SELECT symbol, current_price, prior_close 
        FROM options_prices 
        WHERE symbol = ?
        """
        result = pd.read_sql_query(query, conn, params=[symbol])
        
        if not result.empty:
            print(f"\nFound price for '{symbol}':")
            print(result.to_string(index=False))
        else:
            print(f"\nNo price found for '{symbol}'")
            
            # Try partial match
            partial_query = """
            SELECT symbol, current_price, prior_close 
            FROM options_prices 
            WHERE symbol LIKE ?
            LIMIT 5
            """
            partial_symbol = symbol.split()[0] + '%'
            partial_result = pd.read_sql_query(partial_query, conn, params=[partial_symbol])
            
            if not partial_result.empty:
                print(f"Partial matches for '{partial_symbol}':")
                print(partial_result.to_string(index=False))
    
    conn.close()
    
    # Check TYU5's market price lookup
    print("\n\n4. TYU5 MARKET PRICE LOOKUP TEST")
    print("-" * 60)
    
    # Get unique symbols from trades
    trades_df = adapter.get_trades_for_calculation()
    if not trades_df.empty:
        unique_symbols = trades_df['Symbol'].unique()[:5]  # First 5 for testing
        print(f"\nTesting market price lookup for TYU5 symbols:")
        
        prices_df = adapter.get_market_prices_for_symbols(unique_symbols.tolist())
        
        if not prices_df.empty:
            print("\nPrices found:")
            print(prices_df.to_string(index=False))
        else:
            print("\nNo prices found for any symbols!")
            
        # Show the symbol mapping issue
        print("\n\nSYMBOL MAPPING ISSUE:")
        print("-" * 40)
        print("TYU5 transforms options to CME format (VY3N5 P 109.500)")
        print("But market_prices DB has Bloomberg format (VBYN25P3 109.500 Comdty)")
        print("The reverse mapping in get_market_prices_for_symbols is incomplete!")


if __name__ == "__main__":
    debug_symbol_mapping() 