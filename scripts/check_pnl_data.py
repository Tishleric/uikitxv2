"""Simple script to check P&L data state."""

import sqlite3
import pandas as pd

def check_bad_price():
    """Check for the bad price issue."""
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    
    query = """
    SELECT trade_id, instrument_name, price, quantity 
    FROM processed_trades 
    WHERE instrument_name = 'XCMEOCADPS20250714N0VY2/109'
    """
    
    df = pd.read_sql_query(query, conn)
    print("\nTrades for XCMEOCADPS20250714N0VY2/109:")
    print(df)
    
    conn.close()


def check_eod_unrealized():
    """Check EOD unrealized P&L values."""
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    
    query = """
    SELECT trade_date, 
           SUM(CASE WHEN unrealized_pnl != 0 THEN 1 ELSE 0 END) as non_zero_unrealized,
           COUNT(*) as total_instruments,
           SUM(unrealized_pnl) as total_unrealized
    FROM eod_pnl
    GROUP BY trade_date
    ORDER BY trade_date
    """
    
    df = pd.read_sql_query(query, conn)
    print("\nEOD P&L Summary:")
    print(df)
    
    # Check specific dates
    query2 = """
    SELECT instrument_name, closing_position, unrealized_pnl, total_pnl
    FROM eod_pnl
    WHERE trade_date = '2025-07-12' AND closing_position != 0
    LIMIT 10
    """
    
    df2 = pd.read_sql_query(query2, conn)
    print("\nSample positions for 2025-07-12:")
    print(df2)
    
    conn.close()


if __name__ == "__main__":
    check_bad_price()
    check_eod_unrealized() 