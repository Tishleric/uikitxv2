#!/usr/bin/env python
"""Debug database persistence vs Excel output mismatch."""

import sys
import pandas as pd
import sqlite3
from pathlib import Path
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def debug_database_persistence():
    """Debug why database doesn't have all lot positions from Excel."""
    
    print("=" * 80)
    print("DATABASE PERSISTENCE DEBUG")
    print("=" * 80)
    
    # 1. Find latest Excel file and read breakdown
    excel_files = glob.glob("data/output/pnl/tyu5_pnl_*.xlsx")
    if not excel_files:
        print("No TYU5 Excel files found!")
        return
        
    latest_file = max(excel_files, key=lambda f: Path(f).stat().st_mtime)
    print(f"\nAnalyzing Excel: {latest_file}")
    
    # Read breakdown from Excel
    breakdown_df = pd.read_excel(latest_file, sheet_name='Position_Breakdown')
    excel_symbols = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']['Symbol'].unique()
    
    print(f"\nExcel breakdown has {len(excel_symbols)} symbols with lots:")
    for symbol in sorted(excel_symbols):
        lot_count = len(breakdown_df[(breakdown_df['Symbol'] == symbol) & (breakdown_df['Label'] == 'OPEN_POSITION')])
        print(f"  - {symbol}: {lot_count} lots")
    
    # 2. Check database lot_positions
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    # Query lot positions
    lot_query = """
    SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    lot_df = pd.read_sql_query(lot_query, conn)
    
    print(f"\n\nDatabase lot_positions has {len(lot_df)} symbols:")
    print(lot_df.to_string(index=False))
    
    db_symbols = set(lot_df['symbol'].tolist()) if not lot_df.empty else set()
    
    # 3. Compare and analyze gap
    print("\n\nGAP ANALYSIS:")
    print("-" * 60)
    
    missing_in_db = set(excel_symbols) - db_symbols
    
    if missing_in_db:
        print(f"\nSymbols in Excel but NOT in database ({len(missing_in_db)}):")
        for symbol in sorted(missing_in_db):
            print(f"  - {symbol}")
            
            # Check positions table to see if symbol format mismatch
            pos_query = """
            SELECT instrument_name, position_quantity 
            FROM positions 
            WHERE instrument_name LIKE ?
            """
            
            # Try different variations
            variations = [
                f"%{symbol}%",  # Contains
                f"{symbol}%",   # Starts with
                f"%{symbol}"    # Ends with
            ]
            
            found = False
            for variation in variations:
                pos_result = pd.read_sql_query(pos_query, conn, params=[variation])
                if not pos_result.empty:
                    print(f"    → Found in positions table as: {pos_result['instrument_name'].iloc[0]}")
                    found = True
                    break
                    
            if not found:
                print(f"    → NOT found in positions table at all!")
    
    # 4. Check exact symbol formats
    print("\n\n4. SYMBOL FORMAT ANALYSIS:")
    print("-" * 60)
    
    # Get all symbols from positions table
    pos_symbols_query = "SELECT DISTINCT instrument_name FROM positions WHERE position_quantity != 0"
    positions_df = pd.read_sql_query(pos_symbols_query, conn)
    
    print("\nPositions table symbols:")
    for symbol in positions_df['instrument_name']:
        print(f"  - {symbol}")
        
    print("\nBreakdown symbols (from Excel):")
    for symbol in sorted(excel_symbols):
        print(f"  - {symbol}")
    
    print("\n\nSYMBOL MAPPING ISSUE:")
    print("The TYU5DatabaseWriter uses the symbol from breakdown_df directly.")
    print("But breakdown_df has transformed symbols (e.g., 'VY3N5')")
    print("While positions table expects Bloomberg format (e.g., 'VBYN25P3 109.500 Comdty')")
    print("\nThis mismatch prevents proper position_id lookup and lot persistence!")
    
    conn.close()


if __name__ == "__main__":
    debug_database_persistence() 