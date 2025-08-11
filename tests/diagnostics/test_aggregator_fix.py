#!/usr/bin/env python3
"""
Test the positions aggregator fix
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator

def main():
    print("Testing positions aggregator fix...")
    
    # Initialize aggregator
    aggregator = PositionsAggregator()
    
    # Force a reload from database
    aggregator._load_positions_from_db()
    
    # Check results
    df = aggregator.positions_cache
    
    print(f"\nPositions loaded: {len(df)} symbols")
    
    # Show only symbols with closed positions
    closed_df = df[df['closed_position'] > 0]
    
    if not closed_df.empty:
        print("\nSymbols with closed positions (should be 0 for Aug 7):")
        print(closed_df[['symbol', 'closed_position', 'fifo_realized_pnl']].to_string(index=False))
    else:
        print("\n✓ SUCCESS: No closed positions for current trading day (Aug 7)")
    
    # Show open positions (should still be there)
    open_df = df[df['open_position'] != 0]
    
    if not open_df.empty:
        print(f"\nOpen positions (unaffected by fix): {len(open_df)} symbols")
        print(open_df[['symbol', 'open_position']].to_string(index=False))
    
if __name__ == "__main__":
    main()