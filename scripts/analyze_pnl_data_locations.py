#!/usr/bin/env python
"""Analyze all P&L data locations and values in the system."""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_pnl_data():
    """Analyze all P&L data locations."""
    
    print("=" * 80)
    print("P&L DATA ANALYSIS - WHERE IS YOUR P&L STORED?")
    print("=" * 80)
    
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    
    # 1. POSITIONS TABLE - Primary P&L Storage
    print("\n1. POSITIONS TABLE (Primary P&L Storage)")
    print("-" * 60)
    
    query = """
    SELECT 
        instrument_name,
        position_quantity,
        avg_cost,
        last_market_price,
        total_realized_pnl,
        unrealized_pnl,
        closed_quantity,
        (total_realized_pnl + unrealized_pnl) as total_pnl
    FROM positions
    ORDER BY instrument_name
    """
    
    positions_df = pd.read_sql_query(query, conn)
    print(positions_df)
    
    print(f"\nTOTAL P&L: ${positions_df['total_pnl'].sum():,.2f}")
    print(f"  - Realized P&L: ${positions_df['total_realized_pnl'].sum():,.2f}")
    print(f"  - Unrealized P&L: ${positions_df['unrealized_pnl'].sum():,.2f}")
    
    # 2. FULLPNL TABLE - Master P&L Table
    print("\n\n2. FULLPNL TABLE (Master P&L Table)")
    print("-" * 60)
    
    # Check if FULLPNL exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FULLPNL'")
    if cursor.fetchone():
        query = """
        SELECT 
            symbol,
            open_position,
            px_last,
            px_settle,
            delta_f
        FROM FULLPNL
        ORDER BY symbol
        """
        
        fullpnl_df = pd.read_sql_query(query, conn)
        print(fullpnl_df)
    else:
        print("FULLPNL table does not exist")
    
    # 3. LOT_POSITIONS TABLE - Lot-Level Tracking
    print("\n\n3. LOT_POSITIONS TABLE (TYU5 Lot-Level Tracking)")
    print("-" * 60)
    
    query = """
    SELECT 
        symbol,
        COUNT(*) as num_lots,
        SUM(remaining_quantity) as total_quantity,
        AVG(entry_price) as avg_entry_price,
        MIN(entry_price) as min_price,
        MAX(entry_price) as max_price
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    lots_df = pd.read_sql_query(query, conn)
    print(lots_df)
    
    # 4. TYU5 Excel Files
    print("\n\n4. TYU5 EXCEL FILES")
    print("-" * 60)
    
    excel_files = glob.glob("data/output/pnl/tyu5_pnl_*.xlsx")
    if excel_files:
        latest_file = max(excel_files, key=lambda f: Path(f).stat().st_mtime)
        print(f"Latest Excel: {latest_file}")
        
        # Read positions sheet
        try:
            positions_excel = pd.read_excel(latest_file, sheet_name="Positions")
            print(f"\nPositions in Excel: {len(positions_excel)} symbols")
            if 'Total_PNL' in positions_excel.columns:
                print(f"Total P&L in Excel: ${positions_excel['Total_PNL'].sum():,.2f}")
        except:
            print("Could not read Positions sheet from Excel")
    else:
        print("No TYU5 Excel files found")
    
    # 5. Data Flow Summary
    print("\n\n5. DATA FLOW SUMMARY")
    print("-" * 60)
    print("Your P&L data flows through these systems:")
    print("\n1. CSV Trade Files → TradePreprocessor → positions table")
    print("   - Basic FIFO calculation")
    print("   - Stores: realized P&L, unrealized P&L, average cost")
    print("   - Real-time updates as trades are processed")
    
    print("\n2. positions table → TYU5 Engine → Excel + lot_positions table")
    print("   - Advanced FIFO with lot tracking")
    print("   - Bachelier option pricing")
    print("   - Greek calculations")
    print("   - Risk scenarios")
    
    print("\n3. Multiple sources → FULLPNL table (Master table)")
    print("   - Consolidates data from all sources")
    print("   - Adds market prices, Greeks, etc.")
    
    conn.close()

if __name__ == "__main__":
    analyze_pnl_data() 