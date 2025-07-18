#!/usr/bin/env python
"""Test TYU5 persistence directly to ensure fixes are applied."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the service and force reload
import importlib
import lib.trading.pnl_integration.tyu5_service
import lib.trading.pnl_integration.tyu5_database_writer
import lib.trading.pnl.tyu5_pnl.core.breakdown_generator

# Force reload to ensure fixes are applied
importlib.reload(lib.trading.pnl.tyu5_pnl.core.breakdown_generator)
importlib.reload(lib.trading.pnl_integration.tyu5_database_writer)
importlib.reload(lib.trading.pnl_integration.tyu5_service)

from lib.trading.pnl_integration.tyu5_service import TYU5Service

def test_direct_persistence():
    """Test TYU5 persistence directly."""
    
    print("=" * 80)
    print("DIRECT TYU5 PERSISTENCE TEST")
    print("=" * 80)
    
    # Run TYU5 with database writer enabled
    print("\n1. Running TYU5 calculation with DB writer enabled...")
    service = TYU5Service(enable_attribution=False, enable_db_writer=True)
    
    try:
        output_file = service.calculate_pnl(output_format="excel")
        print(f"✓ TYU5 calculation complete: {output_file}")
    except Exception as e:
        print(f"Error during calculation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check database results
    print("\n2. Checking database lot_positions...")
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    lots_df = pd.read_sql_query(query, conn)
    print("\nDatabase lot positions:")
    print(lots_df)
    
    # Check position_id linkage
    print("\n3. Checking position_id linkage...")
    query = """
    SELECT l.symbol, l.position_id, p.instrument_name
    FROM lot_positions l
    LEFT JOIN positions p ON l.position_id = p.id
    ORDER BY l.symbol
    LIMIT 10
    """
    
    linkage_df = pd.read_sql_query(query, conn)
    print("\nPosition linkage:")
    print(linkage_df)
    
    conn.close()
    
    # Check if we have all 5 symbols
    unique_symbols = lots_df['symbol'].nunique() if not lots_df.empty else 0
    print(f"\nTotal unique symbols with lots: {unique_symbols}")
    
    if unique_symbols >= 5:
        print("✓ SUCCESS: Full coverage achieved!")
    else:
        print("✗ Still missing some symbols")
        
    # Check for VY3N5 and WY4N5 specifically
    if 'VY3N5' in lots_df['symbol'].values or 'WY4N5' in lots_df['symbol'].values:
        print("✓ Weekly options (VY3N5/WY4N5) are now persisted!")

if __name__ == "__main__":
    test_direct_persistence() 