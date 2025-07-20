#!/usr/bin/env python
"""Trace P&L calculation methods and data sources in detail."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def trace_pnl_calculations():
    """Trace P&L calculation methods and data sources."""
    
    print("=" * 80)
    print("P&L CALCULATION TRACING")
    print("=" * 80)
    
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    # 1. REALIZED P&L CALCULATION
    print("\n1. REALIZED P&L CALCULATION")
    print("-" * 60)
    print("Method: FIFO (First In, First Out)")
    print("Formula: Realized P&L = (Exit Price - Entry Price) × Quantity")
    print("\nCurrent Status: MOCKED - Returns $0.00")
    print("Reason: CTO_INTEGRATION - Original FIFO logic commented out")
    print("\nOriginal Logic (commented out):")
    print("  - BUY: Covers short positions first, then creates long")
    print("  - SELL: Sells long positions first, then creates short")
    print("  - P&L calculated when position is closed/reduced")
    
    # Check if any trades exist to show example
    cursor = conn.execute("""
        SELECT Symbol, Action, Quantity, Price 
        FROM cto_trades 
        LIMIT 5
    """)
    trades = cursor.fetchall()
    
    if trades:
        print("\nExample trades in system:")
        for trade in trades:
            print(f"  {trade[0]}: {trade[1]} {abs(trade[2])} @ ${trade[3]}")
    
    # 2. UNREALIZED P&L CALCULATION
    print("\n\n2. UNREALIZED P&L CALCULATION")
    print("-" * 60)
    print("Method: Mark-to-Market")
    print("Formula: Unrealized P&L = (Market Price - Average Cost) × Position Quantity")
    print("\nCurrent Status: FUNCTIONAL (when market prices available)")
    
    # Show actual calculation from positions table
    query = """
    SELECT 
        instrument_name,
        position_quantity,
        avg_cost,
        last_market_price,
        unrealized_pnl,
        CASE 
            WHEN position_quantity != 0 AND last_market_price IS NOT NULL 
            THEN ROUND((last_market_price - avg_cost) * position_quantity, 5)
            ELSE NULL
        END as calculated_unrealized
    FROM positions
    WHERE position_quantity != 0
    """
    
    positions_df = pd.read_sql_query(query, conn)
    
    print("\nActual Position Calculations:")
    for idx, row in positions_df.iterrows():
        print(f"\n{row['instrument_name']}:")
        print(f"  Position: {row['position_quantity']}")
        print(f"  Avg Cost: ${row['avg_cost']:.5f}")
        print(f"  Market Price: ${row['last_market_price']:.5f}" if row['last_market_price'] else "  Market Price: None")
        print(f"  Unrealized P&L: ${row['unrealized_pnl']:.2f}")
        if row['calculated_unrealized'] is not None:
            print(f"  Verification: ({row['last_market_price']:.5f} - {row['avg_cost']:.5f}) × {row['position_quantity']} = ${row['calculated_unrealized']:.2f}")
    
    # 3. MARKET PRICE SOURCES
    print("\n\n3. MARKET PRICE DATA SOURCES")
    print("-" * 60)
    
    # Check market_prices table
    query = """
    SELECT 
        COUNT(DISTINCT bloomberg) as unique_symbols,
        COUNT(*) as total_records,
        MIN(upload_timestamp) as earliest,
        MAX(upload_timestamp) as latest
    FROM market_prices
    """
    
    market_stats = pd.read_sql_query(query, conn).iloc[0]
    
    print(f"Market Prices Database:")
    print(f"  Total Records: {market_stats['total_records']:,}")
    print(f"  Unique Symbols: {market_stats['unique_symbols']}")
    print(f"  Date Range: {market_stats['earliest']} to {market_stats['latest']}")
    
    # Show price lookup logic
    print("\nPrice Lookup Logic (get_market_price):")
    print("  1. Maps instrument to Bloomberg symbol")
    print("  2. Searches for most recent price before timestamp")
    print("  3. Prefers px_settle over px_last")
    print("  4. Validates price is numeric (filters '#N/A', etc.)")
    
    # Show example market prices
    query = """
    SELECT 
        bloomberg,
        px_settle,
        px_last,
        upload_timestamp,
        upload_hour
    FROM market_prices
    WHERE bloomberg IN (
        SELECT DISTINCT instrument_name 
        FROM positions 
        WHERE position_quantity != 0
    )
    ORDER BY bloomberg, upload_timestamp DESC
    LIMIT 10
    """
    
    price_df = pd.read_sql_query(query, conn)
    
    if not price_df.empty:
        print("\nSample Market Prices:")
        print(price_df.to_string(index=False))
    
    # 4. DATA FLOW TIMELINE
    print("\n\n4. DATA FLOW TIMELINE")
    print("-" * 60)
    print("1. Trade CSV arrives → TradePreprocessor")
    print("   - Converts Actant format to Bloomberg format")
    print("   - Stores in cto_trades table")
    print("   - Updates positions table (without P&L)")
    print("\n2. Market Price CSV arrives (2pm/4pm)")
    print("   - PX_LAST at 2pm → current_price")
    print("   - PX_SETTLE at 4pm → prior_close") 
    print("   - Stores in market_prices table")
    print("\n3. PositionManager.update_market_prices() called")
    print("   - Queries latest price for each position")
    print("   - Calculates unrealized P&L")
    print("   - Updates positions.unrealized_pnl")
    
    # 5. WHY P&L IS ZERO
    print("\n\n5. WHY YOUR P&L SHOWS $0.00")
    print("-" * 60)
    
    # Check for realized P&L
    realized_sum = conn.execute("SELECT SUM(total_realized_pnl) FROM positions").fetchone()[0] or 0
    print(f"Total Realized P&L: ${realized_sum:.2f}")
    if realized_sum == 0:
        print("  → FIFO calculation is MOCKED (CTO integration pending)")
    
    # Check for unrealized P&L
    unrealized_sum = conn.execute("SELECT SUM(unrealized_pnl) FROM positions").fetchone()[0] or 0
    print(f"\nTotal Unrealized P&L: ${unrealized_sum:.2f}")
    
    if unrealized_sum == 0:
        # Check why
        no_prices = conn.execute("""
            SELECT COUNT(*) FROM positions 
            WHERE position_quantity != 0 AND last_market_price IS NULL
        """).fetchone()[0]
        
        if no_prices > 0:
            print(f"  → {no_prices} positions have no market price")
        
        same_price = conn.execute("""
            SELECT COUNT(*) FROM positions 
            WHERE position_quantity != 0 
            AND last_market_price = avg_cost
        """).fetchone()[0]
        
        if same_price > 0:
            print(f"  → {same_price} positions have market price = avg cost")
    
    # 6. CALCULATION LOCATIONS IN CODE
    print("\n\n6. KEY CODE LOCATIONS")
    print("-" * 60)
    print("Realized P&L:")
    print("  - calculator.py: _process_buy() and _process_sell() [MOCKED]")
    print("  - Original FIFO logic commented with 'CTO_INTEGRATION'")
    print("\nUnrealized P&L:")
    print("  - position_manager.py: update_market_prices() [WORKING]")
    print("  - Line 320: unrealized_pnl = (market_price - avg_cost) * quantity")
    print("\nMarket Price Lookup:")
    print("  - storage.py: get_market_price() [WORKING]")
    print("  - Handles price validation and source selection")
    
    conn.close()

if __name__ == "__main__":
    trace_pnl_calculations() 