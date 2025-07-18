#!/usr/bin/env python
"""Directly update lot_positions from the latest Excel file."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter

def main():
    """Directly update lot_positions from Excel."""
    
    print("=" * 80)
    print("DIRECT LOT POSITIONS UPDATE FROM EXCEL")
    print("=" * 80)
    
    # Find latest Excel file
    excel_files = glob.glob("data/output/pnl/tyu5_pnl_*.xlsx")
    if not excel_files:
        print("No TYU5 Excel files found!")
        return
        
    latest_file = max(excel_files, key=lambda f: Path(f).stat().st_mtime)
    print(f"\nUsing Excel file: {latest_file}")
    
    # Read breakdown sheet
    try:
        breakdown_df = pd.read_excel(latest_file, sheet_name="Position_Breakdown")
        print(f"\nFound {len(breakdown_df)} rows in Position_Breakdown")
        
        # Filter for OPEN_POSITION rows
        open_positions = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']
        print(f"Found {len(open_positions)} OPEN_POSITION rows")
        
        # Count unique symbols
        unique_symbols = open_positions['Symbol'].nunique()
        print(f"Unique symbols with lots: {unique_symbols}")
        print(f"Symbols: {', '.join(open_positions['Symbol'].unique())}")
        
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return
    
    # Initialize database writer and use its method
    db_path = "data/output/pnl/pnl_tracker.db"
    writer = TYU5DatabaseWriter(db_path)
    
    # Get current timestamp
    calc_timestamp = datetime.now()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Use the writer's method to persist lot positions
        writer._write_lot_positions(conn, breakdown_df, calc_timestamp)
        conn.commit()
        print("\nSuccessfully updated lot_positions table")
        
        # Verify the update
        query = """
        SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
        FROM lot_positions
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result_df = pd.read_sql_query(query, conn)
        print("\nUpdated lot_positions:")
        print(result_df)
        print(f"\nTotal symbols with lots: {len(result_df)}")
        
        # Check position_id linkage
        query = """
        SELECT l.symbol, l.position_id, p.instrument_name
        FROM lot_positions l
        LEFT JOIN positions p ON l.position_id = p.id
        WHERE l.symbol IN ('VY3N5', 'WY4N5')
        LIMIT 5
        """
        
        linkage_df = pd.read_sql_query(query, conn)
        print("\nWeekly option linkage:")
        print(linkage_df)
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 