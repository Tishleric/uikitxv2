#!/usr/bin/env python
"""Debug TYU5 Database Writer

This script tests the database writer with actual TYU5 Excel output.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter


def main():
    # Read the latest TYU5 Excel file
    excel_file = "data/output/pnl/tyu5_pnl_all_20250717_193940.xlsx"
    print(f"Reading Excel file: {excel_file}")
    
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    print(f"Sheets: {list(excel_data.keys())}")
    
    # Extract dataframes
    positions_df = excel_data.get('Positions', pd.DataFrame())
    trades_df = excel_data.get('Trades', pd.DataFrame())
    breakdown_df = excel_data.get('Position_Breakdown', pd.DataFrame())
    risk_df = excel_data.get('Risk_Matrix', pd.DataFrame())
    
    print(f"\nPositions: {len(positions_df)} rows")
    print(f"Trades: {len(trades_df)} rows")
    print(f"Breakdown: {len(breakdown_df)} rows")
    print(f"Risk Matrix: {len(risk_df)} rows")
    
    # Show breakdown structure
    print("\nPosition_Breakdown sample:")
    print(breakdown_df.head())
    print(f"\nUnique Labels: {breakdown_df['Label'].unique() if 'Label' in breakdown_df else 'No Label column'}")
    
    # Filter for OPEN_POSITION
    if 'Label' in breakdown_df:
        open_positions = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']
        print(f"\nOPEN_POSITION rows: {len(open_positions)}")
        if not open_positions.empty:
            print(open_positions[['Symbol', 'Description', 'Quantity', 'Price']].head())
    
    # Test the writer
    writer = TYU5DatabaseWriter()
    calc_timestamp = datetime.now()
    
    print(f"\nAttempting to write to database...")
    success = writer.write_results(
        positions_df=positions_df,
        trades_df=trades_df,
        breakdown_df=breakdown_df,
        risk_df=risk_df,
        calc_timestamp=calc_timestamp
    )
    
    print(f"Write success: {success}")
    
    # Check what was written
    import sqlite3
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM lot_positions")
    print(f"\nlot_positions: {cursor.fetchone()[0]} records")
    
    cursor.execute("SELECT COUNT(*) FROM risk_scenarios")
    print(f"risk_scenarios: {cursor.fetchone()[0]} records")
    
    conn.close()


if __name__ == "__main__":
    main() 