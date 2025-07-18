#!/usr/bin/env python
"""Debug why options are not persisted to database."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def debug_persistence():
    """Debug why options are not persisted."""
    
    print("=" * 80)
    print("DEBUG OPTIONS PERSISTENCE")
    print("=" * 80)
    
    # Connect to database
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    # 1. Check positions table for options
    print("\n1. OPTIONS IN POSITIONS TABLE")
    print("-" * 60)
    
    query = """
    SELECT id, symbol, quantity, current_price, updated_at
    FROM positions
    WHERE symbol LIKE 'VBY%' OR symbol LIKE 'TYW%' OR symbol LIKE 'TJP%'
    ORDER BY symbol
    """
    
    positions_df = pd.read_sql_query(query, conn)
    print(positions_df)
    
    # 2. Check if positions exist for VBYN25P3 and TYWN25P4
    print("\n\n2. LOOKING FOR SPECIFIC OPTIONS")
    print("-" * 60)
    
    query = """
    SELECT id, symbol, quantity
    FROM positions
    WHERE symbol LIKE 'VBYN25P3%' OR symbol LIKE 'TYWN25P4%'
    """
    
    specific_df = pd.read_sql_query(query, conn)
    print(f"\nFound {len(specific_df)} matching positions:")
    print(specific_df)
    
    # 3. Check all unique symbols in positions
    print("\n\n3. ALL UNIQUE SYMBOLS IN POSITIONS")
    print("-" * 60)
    
    query = """
    SELECT DISTINCT symbol
    FROM positions
    ORDER BY symbol
    """
    
    all_symbols_df = pd.read_sql_query(query, conn)
    print(f"\nTotal unique symbols: {len(all_symbols_df)}")
    print(all_symbols_df)
    
    # 4. Check lot_positions for the problematic symbols
    print("\n\n4. LOT_POSITIONS CONTENT")
    print("-" * 60)
    
    query = """
    SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    lots_df = pd.read_sql_query(query, conn)
    print(lots_df)
    
    # 5. Check if the mapping function would work
    print("\n\n5. SYMBOL MAPPING TEST")
    print("-" * 60)
    
    from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter
    
    writer = TYU5DatabaseWriter(db_path)
    
    test_symbols = ["VY3N5", "WY4N5"]
    for symbol in test_symbols:
        mapped = writer._map_symbol_to_bloomberg(symbol)
        print(f"{symbol} -> {mapped}")
        
        # Check if this mapped symbol exists in positions
        query = """
        SELECT id, symbol
        FROM positions
        WHERE symbol LIKE ? || '%'
        """
        
        cursor = conn.execute(query, (mapped,))
        results = cursor.fetchall()
        
        if results:
            print(f"  Found positions: {results}")
        else:
            print(f"  NO POSITIONS FOUND for {mapped}")
            
    conn.close()

if __name__ == "__main__":
    debug_persistence() 