#!/usr/bin/env python
"""Check TYU5 Excel output to understand position breakdown."""

import sys
import pandas as pd
from pathlib import Path
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_tyu5_excel():
    """Examine TYU5 Excel output files."""
    
    print("=" * 80)
    print("TYU5 EXCEL OUTPUT ANALYSIS")
    print("=" * 80)
    
    # Find latest TYU5 Excel file
    excel_files = glob.glob("data/output/pnl/tyu5_pnl_*.xlsx")
    
    if not excel_files:
        print("No TYU5 Excel files found!")
        return
        
    # Get most recent file
    latest_file = max(excel_files, key=lambda f: Path(f).stat().st_mtime)
    print(f"\nAnalyzing: {latest_file}")
    
    # Read all sheets
    excel_data = pd.read_excel(latest_file, sheet_name=None)
    
    print(f"\nSheets in Excel file: {list(excel_data.keys())}")
    
    # 1. Check Positions sheet
    if 'Positions' in excel_data:
        positions_df = excel_data['Positions']
        print("\n1. POSITIONS SHEET")
        print("-" * 60)
        print(f"Total positions: {len(positions_df)}")
        print("\nPositions overview:")
        print(positions_df[['Symbol', 'Type', 'Net_Quantity', 'Avg_Entry_Price']].to_string(index=False))
    
    # 2. Check Position_Breakdown sheet
    if 'Position_Breakdown' in excel_data:
        breakdown_df = excel_data['Position_Breakdown']
        print("\n\n2. POSITION_BREAKDOWN SHEET")
        print("-" * 60)
        print(f"Total breakdown rows: {len(breakdown_df)}")
        
        # Count by label
        label_counts = breakdown_df['Label'].value_counts()
        print("\nBreakdown by label:")
        for label, count in label_counts.items():
            print(f"  - {label}: {count}")
            
        # Show symbols with breakdown
        breakdown_symbols = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']['Symbol'].unique()
        print(f"\nSymbols with lot breakdown ({len(breakdown_symbols)}):")
        for symbol in sorted(breakdown_symbols):
            lot_count = len(breakdown_df[(breakdown_df['Symbol'] == symbol) & (breakdown_df['Label'] == 'OPEN_POSITION')])
            print(f"  - {symbol}: {lot_count} lots")
            
        # Show some actual lot details
        print("\nSample lot details:")
        open_positions = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION'].head(10)
        if not open_positions.empty:
            print(open_positions[['Symbol', 'Description', 'Quantity', 'Price']].to_string(index=False))
    
    # 3. Check which symbols are missing from breakdown
    if 'Positions' in excel_data and 'Position_Breakdown' in excel_data:
        print("\n\n3. COVERAGE ANALYSIS")
        print("-" * 60)
        
        positions_symbols = set(positions_df['Symbol'].unique())
        breakdown_symbols = set(breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION']['Symbol'].unique())
        
        missing_symbols = positions_symbols - breakdown_symbols
        
        if missing_symbols:
            print(f"\nPositions WITHOUT lot breakdown ({len(missing_symbols)}):")
            for symbol in sorted(missing_symbols):
                pos_row = positions_df[positions_df['Symbol'] == symbol].iloc[0]
                print(f"  - {symbol}: {pos_row['Net_Quantity']} quantity, Type={pos_row['Type']}")
                
    # 4. Check Trades sheet for insights
    if 'Trades' in excel_data:
        trades_df = excel_data['Trades']
        print("\n\n4. TRADES ANALYSIS")
        print("-" * 60)
        print(f"Total trades: {len(trades_df)}")
        
        # Count trades by symbol
        trade_counts = trades_df['Symbol'].value_counts()
        print("\nTrades per symbol:")
        for symbol, count in trade_counts.items():
            print(f"  - {symbol}: {count} trades")
            
        # Check if all symbols have trades
        if 'Positions' in excel_data:
            positions_symbols = set(positions_df['Symbol'].unique())
            trades_symbols = set(trades_df['Symbol'].unique())
            
            symbols_without_trades = positions_symbols - trades_symbols
            if symbols_without_trades:
                print(f"\nPositions WITHOUT trades in this Excel: {symbols_without_trades}")


if __name__ == "__main__":
    check_tyu5_excel() 