"""
Trace how trades flow through the system to find where cross-symbol matching happens
"""
import sqlite3
import pandas as pd
from datetime import datetime

def trace_processing_flow(db_path='trades.db'):
    """Trace the flow of trades through the system"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("TRADE PROCESSING FLOW ANALYSIS")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Check if there are any weird patterns in the data
    print("### 1. Checking for Symbol Inconsistencies ###")
    
    # Look for trades where realized symbol doesn't match either trade
    weird_query = """
    SELECT DISTINCT
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.sequenceIdDoingOffsetting,
        t1.symbol as offset_trade_symbol,
        t2.symbol as offsetting_trade_symbol,
        r.timestamp
    FROM realized_fifo r
    LEFT JOIN (
        SELECT sequenceId, symbol FROM trades_fifo
        UNION ALL
        SELECT sequenceId, symbol FROM trades_lifo
    ) t1 ON r.sequenceIdBeingOffset = t1.sequenceId
    LEFT JOIN (
        SELECT sequenceId, symbol FROM trades_fifo
        UNION ALL
        SELECT sequenceId, symbol FROM trades_lifo
    ) t2 ON r.sequenceIdDoingOffsetting = t2.sequenceId
    WHERE DATE(r.timestamp) >= DATE('now', '-5 days')
    ORDER BY r.timestamp DESC
    LIMIT 20
    """
    
    weird = pd.read_sql_query(weird_query, conn)
    
    print("\nRealized trades with their original symbols:")
    print(weird.to_string(index=False))
    
    # Check if realized symbol matches the offsetting trade
    weird['matches_offsetting'] = weird['realized_symbol'] == weird['offsetting_trade_symbol']
    weird['matches_offset'] = weird['realized_symbol'] == weird['offset_trade_symbol']
    
    print("\n### 2. Symbol Matching Analysis ###")
    print(f"Realized symbol matches offsetting trade: {weird['matches_offsetting'].sum()}/{len(weird)}")
    print(f"Realized symbol matches offset trade: {weird['matches_offset'].sum()}/{len(weird)}")
    
    # Look for the specific pattern
    print("\n### 3. Investigating the Pattern ###")
    
    pattern_query = """
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_realizations,
        COUNT(DISTINCT sequenceIdDoingOffsetting) as unique_offsetting,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols
    FROM realized_fifo
    WHERE DATE(timestamp) >= DATE('now', '-5 days')
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    """
    
    pattern = pd.read_sql_query(pattern_query, conn)
    print("\nDaily realization patterns:")
    print(pattern.to_string(index=False))
    
    # Check what happened to specific trades
    print("\n### 4. Specific Trade Investigation ###")
    
    # Check the USU5 trades that were wrongly matched
    specific_query = """
    SELECT 
        'Original Trade' as status,
        sequenceId,
        symbol,
        buySell,
        quantity,
        price,
        time
    FROM trades_fifo
    WHERE sequenceId IN ('20250801-473', '20250801-474')
    
    UNION ALL
    
    SELECT 
        'Realized As' as status,
        sequenceIdBeingOffset as sequenceId,
        symbol,
        'realized' as buySell,
        SUM(quantity) as quantity,
        AVG(entryPrice) as price,
        MAX(timestamp) as time
    FROM realized_fifo
    WHERE sequenceIdBeingOffset IN ('20250801-473', '20250801-474')
    GROUP BY sequenceIdBeingOffset, symbol
    
    ORDER BY sequenceId, status
    """
    
    specific = pd.read_sql_query(specific_query, conn)
    
    print("\nWhat happened to USU5 trades 20250801-473 and 20250801-474:")
    if len(specific) > 0:
        print(specific.to_string(index=False))
    else:
        print("These trades not found in trades_fifo (already fully realized)")
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    trace_processing_flow()