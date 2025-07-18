#!/usr/bin/env python
"""Check why TYU5 database persistence is failing."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter

def check_persistence_error():
    """Check why database persistence is failing."""
    
    print("=" * 80)
    print("CHECK TYU5 PERSISTENCE ERROR")
    print("=" * 80)
    
    # Find latest Excel file
    excel_files = glob.glob("data/output/pnl/tyu5_pnl_*.xlsx")
    if not excel_files:
        print("No TYU5 Excel files found!")
        return
        
    latest_file = max(excel_files, key=lambda f: Path(f).stat().st_mtime)
    print(f"\nAnalyzing: {latest_file}")
    
    # Initialize database writer
    db_path = "data/output/pnl/pnl_tracker.db"
    writer = TYU5DatabaseWriter(db_path)
    
    # Try to persist with the latest Excel file
    try:
        print("\nTrying to persist from Excel file...")
        success = writer.write_from_excel(latest_file)
        print(f"Success: {success}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    # Check what's in the positions table
    print("\n\nChecking positions table for weekly options:")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT id, instrument_name, position_quantity
    FROM positions
    WHERE instrument_name LIKE 'VBY%' OR instrument_name LIKE 'TYW%'
       OR instrument_name LIKE '3M%' OR instrument_name LIKE 'TJP%'
    ORDER BY instrument_name
    """
    
    df = pd.read_sql_query(query, conn)
    print(df)
    
    # Check if the mapping is working
    print("\n\nChecking symbol mapping:")
    test_symbols = ["VY3N5", "WY4N5"]
    for symbol in test_symbols:
        mapped = writer._map_symbol_to_bloomberg(symbol)
        print(f"\n{symbol} -> {mapped}")
        
        # Check if we can find a position
        cursor = conn.execute("""
            SELECT id, instrument_name
            FROM positions
            WHERE instrument_name LIKE ? || '%'
            LIMIT 5
        """, (mapped,))
        
        results = cursor.fetchall()
        if results:
            print(f"  Found positions: {results}")
        else:
            print(f"  NO POSITIONS FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_persistence_error() 