#!/usr/bin/env python3
"""
Check positions table after the fix
"""

import sqlite3
import pandas as pd
import os

def main():
    print("Checking positions table after aggregator fix...")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'trades.db')
    conn = sqlite3.connect(db_path)
    
    # Query positions table
    query = """
    SELECT 
        symbol,
        open_position,
        closed_position,
        fifo_realized_pnl,
        last_updated
    FROM positions
    ORDER BY symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    print(f"\nTotal positions in table: {len(df)}")
    
    # Show closed positions
    closed_df = df[df['closed_position'] > 0]
    
    if not closed_df.empty:
        print(f"\nPositions with closed_position > 0: {len(closed_df)}")
        print(closed_df.to_string(index=False))
    else:
        print("\n✓ No closed positions in positions table")
    
    # Show open positions
    open_df = df[df['open_position'] != 0]
    
    if not open_df.empty:
        print(f"\n\nOpen positions (should still be present): {len(open_df)}")
        print(open_df[['symbol', 'open_position']].to_string(index=False))
    
    # Check last update time
    if not df.empty:
        last_update = df['last_updated'].max()
        print(f"\n\nLast update: {last_update}")
        print("\nNote: If positions aggregator hasn't run since the fix,")
        print("closed positions may still show. Restart the aggregator service.")
    
    conn.close()

if __name__ == "__main__":
    main()