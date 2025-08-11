#!/usr/bin/env python3
"""
Diagnostic script to demonstrate positions aggregator date filtering bug.
Shows how the aggregator ignores get_trading_day() and uses DATE('now', 'localtime') instead.
"""

import sqlite3
import sys
import os
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from lib.trading.pnl_fifo_lifo.data_manager import get_trading_day

def main():
    print("=" * 80)
    print("POSITIONS AGGREGATOR DATE FILTERING BUG DEMONSTRATION")
    print("=" * 80)
    
    # Connect to trades.db
    db_path = os.path.join(project_root, 'trades.db')
    if not os.path.exists(db_path):
        print(f"ERROR: trades.db not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 1. Show the date discrepancy
    print("\n1. DATE COMPARISON:")
    print("-" * 50)
    
    # Get Python's calculated trading day
    now = datetime.now()
    trading_day = get_trading_day(now)
    print(f"Python datetime.now():        {now}")
    print(f"get_trading_day(now):        {trading_day}")
    
    # Get SQLite's current date
    cursor = conn.cursor()
    cursor.execute("SELECT DATE('now', 'localtime') as sqlite_now")
    sqlite_now = cursor.fetchone()[0]
    print(f"SQLite DATE('now','localtime'): {sqlite_now}")
    
    # Show the problem
    if str(trading_day) != sqlite_now:
        print(f"\n⚠️  MISMATCH: Trading day ({trading_day}) != SQLite now ({sqlite_now})")
    else:
        print(f"\n✓ Dates match (no issue would occur)")
    
    # 2. Show sample data from realized tables
    print("\n\n2. SAMPLE REALIZED TRADES:")
    print("-" * 50)
    
    # Get a few realized trades to show their dates
    query = """
    SELECT 
        symbol,
        DATE(timestamp) as trade_date,
        DATE(timestamp, 
             CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                  THEN '+1 day' 
                  ELSE '+0 day' 
             END) as trading_day,
        COUNT(*) as trades,
        SUM(realizedPnL) as total_pnl
    FROM realized_fifo
    GROUP BY symbol, trading_day
    ORDER BY trading_day DESC
    LIMIT 10
    """
    
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        print("\nRealized FIFO trades by trading day:")
        print(df.to_string(index=False))
    else:
        print("No realized trades found")
    
    # 3. Demonstrate the filtering issue
    print("\n\n3. FILTERING COMPARISON:")
    print("-" * 50)
    
    # Current (buggy) query - using DATE('now', 'localtime')
    buggy_query = """
    SELECT 
        symbol,
        COUNT(*) as trade_count,
        SUM(ABS(quantity)) as closed_quantity,
        SUM(realizedPnL) as realized_pnl
    FROM realized_fifo
    WHERE 
        DATE(timestamp, 
             CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                  THEN '+1 day' 
                  ELSE '+0 day' 
             END) = DATE('now', 'localtime')
    GROUP BY symbol
    """
    
    print(f"\nCURRENT LOGIC (filtering for {sqlite_now}):")
    df_buggy = pd.read_sql_query(buggy_query, conn)
    if not df_buggy.empty:
        print(df_buggy.to_string(index=False))
        print(f"Total symbols: {len(df_buggy)}")
    else:
        print("No trades match DATE('now', 'localtime')")
    
    # Fixed query - using calculated trading day
    fixed_query = f"""
    SELECT 
        symbol,
        COUNT(*) as trade_count,
        SUM(ABS(quantity)) as closed_quantity,
        SUM(realizedPnL) as realized_pnl
    FROM realized_fifo
    WHERE 
        DATE(timestamp, 
             CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                  THEN '+1 day' 
                  ELSE '+0 day' 
             END) = '{trading_day}'
    GROUP BY symbol
    """
    
    print(f"\nFIXED LOGIC (filtering for {trading_day}):")
    df_fixed = pd.read_sql_query(fixed_query, conn)
    if not df_fixed.empty:
        print(df_fixed.to_string(index=False))
        print(f"Total symbols: {len(df_fixed)}")
    else:
        print(f"No trades match trading day {trading_day}")
    
    # 4. Show ALL closed positions that appear due to bug
    print("\n\n4. ALL HISTORICAL CLOSED POSITIONS (What Dashboard Shows):")
    print("-" * 50)
    
    all_query = """
    SELECT 
        s.symbol,
        cf.closed_position,
        cf.fifo_realized_pnl
    FROM (
        SELECT DISTINCT symbol FROM realized_fifo
    ) s
    LEFT JOIN (
        SELECT 
            symbol,
            SUM(ABS(quantity)) as closed_position,
            SUM(realizedPnL) as fifo_realized_pnl
        FROM realized_fifo
        GROUP BY symbol
    ) cf ON s.symbol = cf.symbol
    WHERE cf.closed_position > 0
    ORDER BY s.symbol
    """
    
    df_all = pd.read_sql_query(all_query, conn)
    if not df_all.empty:
        print("\nALL symbols with ANY historical closed positions:")
        print(df_all.to_string(index=False))
        print(f"\nTotal symbols with closed positions: {len(df_all)}")
    
    # 5. Summary
    print("\n\n5. SUMMARY:")
    print("-" * 50)
    print(f"• Positions aggregator calculates trading_day = {trading_day}")
    print(f"• But SQL query uses DATE('now', 'localtime') = {sqlite_now}")
    print(f"• Result: {len(df_all) if not df_all.empty else 0} historical closed positions shown instead of {len(df_fixed) if not df_fixed.empty else 0}")
    print("\nThe fix: Use the calculated trading_day variable in the SQL query")
    print("Line 70 calculates it correctly, but it's never used in the WHERE clauses!")
    
    conn.close()

if __name__ == "__main__":
    main()