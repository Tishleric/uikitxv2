#!/usr/bin/env python
"""Test if the TYU5 fix resolves lot tracking gap."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_service import TYU5Service
from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter
import pandas as pd
import sqlite3


def test_tyu5_fix():
    """Test if the fix resolves lot tracking gap."""
    
    print("=" * 80)
    print("TESTING TYU5 LOT TRACKING FIX")
    print("=" * 80)
    
    # 1. Run TYU5 calculation
    print("\n1. Running TYU5 calculation...")
    service = TYU5Service(enable_attribution=False, enable_db_writer=True)
    
    output_file = service.calculate_pnl(output_format="excel")
    
    if not output_file:
        print("ERROR: TYU5 calculation failed")
        return
        
    print(f"✓ TYU5 calculation complete: {output_file}")
    
    # 2. Check Excel output
    print("\n2. Checking Excel breakdown...")
    
    excel_data = pd.read_excel(output_file, sheet_name=None)
    
    if 'Position_Breakdown' in excel_data:
        breakdown_df = excel_data['Position_Breakdown']
        
        # Count symbols with lot breakdown
        breakdown_symbols = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']['Symbol'].unique()
        print(f"\nSymbols with lot breakdown: {len(breakdown_symbols)}")
        
        for symbol in sorted(breakdown_symbols):
            lot_count = len(breakdown_df[(breakdown_df['Symbol'] == symbol) & (breakdown_df['Label'] == 'OPEN_POSITION')])
            print(f"  - {symbol}: {lot_count} lots")
            
        # Check if VY3N5 and WY4N5 now have lots
        if 'VY3N5' in breakdown_symbols:
            print("\n✓ SUCCESS: VY3N5 now has lot tracking!")
        else:
            print("\n✗ FAILED: VY3N5 still missing lot tracking")
            
        if 'WY4N5' in breakdown_symbols:
            print("✓ SUCCESS: WY4N5 now has lot tracking!")
        else:
            print("✗ FAILED: WY4N5 still missing lot tracking")
    
    # 3. Check database persistence
    print("\n\n3. Checking database lot_positions...")
    
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    lot_df = pd.read_sql_query(query, conn)
    print("\nDatabase lot positions:")
    print(lot_df.to_string(index=False))
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 80)
    print("FIX ASSESSMENT")
    print("=" * 80)
    
    if len(breakdown_symbols) >= 5:  # Should have at least 5 symbols with lots
        print("✓ Fix appears successful - lot tracking coverage improved!")
        print(f"  Coverage: {len(breakdown_symbols)} symbols with lot tracking")
    else:
        print("✗ Fix may not be working - still have gap")
        print(f"  Only {len(breakdown_symbols)} symbols with lot tracking")


if __name__ == "__main__":
    test_tyu5_fix() 