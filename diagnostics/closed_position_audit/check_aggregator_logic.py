"""
Check if PositionsAggregator or price updates are triggering re-realization
"""
import sqlite3
import pandas as pd
from datetime import datetime

def check_aggregator_correlation(db_path='trades.db'):
    """Check if duplicate realizations correlate with price updates or aggregator runs"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("AGGREGATOR AND PRICE UPDATE CORRELATION")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Check pricing table updates for the affected symbol/time
    print("### Price Updates for USU5 on 2025-08-04 ###")
    
    price_query = """
    SELECT 
        symbol,
        price_type,
        price,
        timestamp,
        strftime('%H:%M:%S', timestamp) as time_only
    FROM pricing
    WHERE symbol = 'USU5 Comdty'
      AND DATE(timestamp) = '2025-08-04'
      AND price_type = 'now'
    ORDER BY timestamp
    LIMIT 20
    """
    
    prices = pd.read_sql_query(price_query, conn)
    
    if len(prices) > 0:
        print("\nPrice updates:")
        print(prices[['time_only', 'price', 'price_type']].to_string(index=False))
    
    # Compare with duplicate realization times
    print("\n### Comparing with Duplicate Realization Times ###")
    
    realization_times = """
    SELECT 
        strftime('%H:%M:%S', timestamp) as realization_time,
        exitPrice,
        realizedPnL
    FROM realized_fifo
    WHERE sequenceIdBeingOffset = '20250801-474' 
      AND sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY timestamp
    """
    
    realizations = pd.read_sql_query(realization_times, conn)
    
    print("\nRealization times and exit prices:")
    print(realizations.to_string(index=False))
    
    # Check positions table updates
    print("\n### Positions Table Updates ###")
    
    positions_query = """
    SELECT 
        symbol,
        closed_position,
        last_updated,
        strftime('%H:%M:%S', last_updated) as update_time
    FROM positions
    WHERE symbol IN ('USU5 Comdty', 'TYU5 Comdty')
    ORDER BY last_updated DESC
    """
    
    positions = pd.read_sql_query(positions_query, conn)
    
    print("\nRecent positions table updates:")
    print(positions.to_string(index=False))
    
    # Check if there's a pattern in trades_fifo that might trigger re-processing
    print("\n### Checking trades_fifo Status ###")
    
    trades_status = """
    SELECT 
        sequenceId,
        symbol,
        quantity,
        filled,
        working,
        timestamp
    FROM trades_fifo
    WHERE symbol = 'USU5 Comdty'
      AND (sequenceId = '20250804-478' OR sequenceId = '20250801-474')
    ORDER BY timestamp DESC
    """
    
    trades = pd.read_sql_query(trades_status, conn)
    
    print("\nTrades status:")
    print(trades.to_string(index=False))
    
    # Check if any of these trades have unusual status
    open_trades = """
    SELECT 
        symbol,
        COUNT(*) as total_trades,
        SUM(CASE WHEN filled = working THEN 1 ELSE 0 END) as fully_filled,
        SUM(CASE WHEN filled < working THEN 1 ELSE 0 END) as partially_filled,
        SUM(CASE WHEN filled > working THEN 1 ELSE 0 END) as over_filled
    FROM trades_fifo
    WHERE symbol IN ('USU5 Comdty', 'TYU5 Comdty')
    GROUP BY symbol
    """
    
    status_summary = pd.read_sql_query(open_trades, conn)
    
    print("\n### Trade Status Summary ###")
    print(status_summary.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_aggregator_correlation()