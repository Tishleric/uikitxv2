#!/usr/bin/env python3
"""Debug the exact query for options."""
import sqlite3
from pathlib import Path

def debug_options_query():
    project_root = Path(__file__).parent.parent.parent
    market_prices_db_path = project_root / "data/output/market_prices/market_prices.db"
    
    conn = sqlite3.connect(market_prices_db_path)
    cursor = conn.cursor()
    
    # Test the exact query for one option
    symbol = '3MN5P 110.000 Comdty'
    
    print(f"Testing query for: {symbol}")
    print("="*60)
    
    # First, show all records for this symbol
    cursor.execute("""
        SELECT * FROM options_prices WHERE symbol = ?
    """, (symbol,))
    
    print("All records:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # Now test the exact query from our script
    print("\nQuery with trade_date = '2025-07-16':")
    cursor.execute("""
        SELECT prior_close 
        FROM options_prices 
        WHERE symbol = ? 
        AND trade_date = '2025-07-16'
        ORDER BY last_updated DESC
        LIMIT 1
    """, (symbol,))
    
    result = cursor.fetchone()
    print(f"Result: {result}")
    
    if result and result[0] is not None:
        print(f"prior_close value: {result[0]}")
    else:
        print("No result or NULL prior_close")
    
    conn.close()

if __name__ == "__main__":
    debug_options_query() 