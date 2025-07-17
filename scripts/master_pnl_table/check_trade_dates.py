#!/usr/bin/env python3
"""Check trade dates in our data."""
import sqlite3
from pathlib import Path

def check_trade_dates():
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    market_prices_db_path = project_root / "data/output/market_prices/market_prices.db"
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    # Attach market prices database
    cursor.execute(f"ATTACH DATABASE '{market_prices_db_path}' AS market_prices")
    
    # Check what trade date was used for px_last
    print("Checking px_last sources...")
    
    # For futures
    cursor.execute("""
        SELECT f.symbol, fp.trade_date, fp.current_price, fp.prior_close, fp.last_updated
        FROM FULLPNL f
        JOIN market_prices.futures_prices fp ON f.symbol = 'TYU5 Comdty' AND fp.symbol = 'TYU5'
        WHERE f.symbol = 'TYU5 Comdty'
        ORDER BY fp.last_updated DESC
    """)
    
    print("\nTYU5 Futures data:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # For a sample option
    cursor.execute("""
        SELECT f.symbol, op.trade_date, op.current_price, op.prior_close, op.last_updated
        FROM FULLPNL f
        JOIN market_prices.options_prices op ON f.symbol = op.symbol
        WHERE f.symbol = '3MN5P 110.000 Comdty'
        ORDER BY op.last_updated DESC
    """)
    
    print("\n3MN5P 110.000 Option data:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # Let's see what the latest trade_date is
    cursor.execute("""
        SELECT MAX(trade_date) FROM market_prices.futures_prices
    """)
    print(f"\nLatest futures trade date: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT MAX(trade_date) FROM market_prices.options_prices
    """)
    print(f"Latest options trade date: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    check_trade_dates() 