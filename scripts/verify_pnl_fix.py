#!/usr/bin/env python
"""Verify P&L fix worked correctly."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.storage import PnLStorage

def main():
    """Check if P&L calculations are now correct."""
    storage = PnLStorage()
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    print("P&L FIX VERIFICATION")
    print("=" * 80)
    
    # 1. Check EOD P&L summary by date
    print("\n1. EOD P&L Summary by Date:")
    print("-" * 60)
    cursor.execute("""
        SELECT 
            trade_date,
            COUNT(DISTINCT instrument_name) as instruments,
            SUM(trades_count) as total_trades,
            SUM(realized_pnl) as total_realized,
            SUM(unrealized_pnl) as total_unrealized
        FROM eod_pnl
        GROUP BY trade_date
        ORDER BY trade_date
    """)
    
    print(f"{'Date':<12} {'Instruments':<12} {'Trades':<10} {'Realized':<12} {'Unrealized':<12}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        print(f"{row['trade_date']:<12} {row['instruments']:<12} {row['total_trades']:<10} "
              f"{row['total_realized']:>12.2f} {row['total_unrealized']:>12.2f}")
    
    # 2. Check XCMEFFDPSX20250919U0ZN specifically
    print("\n\n2. XCMEFFDPSX20250919U0ZN P&L Details:")
    print("-" * 60)
    cursor.execute("""
        SELECT trade_date, closing_position, realized_pnl, unrealized_pnl, trades_count
        FROM eod_pnl
        WHERE instrument_name = 'XCMEFFDPSX20250919U0ZN'
        ORDER BY trade_date
    """)
    
    print(f"{'Date':<12} {'Position':<10} {'Trades':<10} {'Realized':<12} {'Unrealized':<12}")
    print("-" * 60)
    found_realized = False
    for row in cursor.fetchall():
        print(f"{row['trade_date']:<12} {row['closing_position']:<10} {row['trades_count']:<10} "
              f"{row['realized_pnl']:>12.2f} {row['unrealized_pnl']:>12.2f}")
        if row['realized_pnl'] != 0:
            found_realized = True
    
    # 3. Check other instruments with realized P&L
    print("\n\n3. All Instruments with Non-Zero Realized P&L:")
    print("-" * 60)
    cursor.execute("""
        SELECT 
            trade_date,
            instrument_name,
            realized_pnl,
            unrealized_pnl,
            closing_position
        FROM eod_pnl
        WHERE realized_pnl != 0
        ORDER BY ABS(realized_pnl) DESC
        LIMIT 10
    """)
    
    print(f"{'Date':<12} {'Instrument':<30} {'Position':<10} {'Realized':<12}")
    print("-" * 60)
    realized_count = 0
    for row in cursor.fetchall():
        realized_count += 1
        instrument = row['instrument_name']
        if len(instrument) > 30:
            instrument = instrument[:27] + "..."
        print(f"{row['trade_date']:<12} {instrument:<30} {row['closing_position']:<10} "
              f"{row['realized_pnl']:>12.2f}")
    
    # 4. Summary
    print("\n\n4. VERIFICATION SUMMARY:")
    print("-" * 60)
    
    # Check if realized P&L is working
    cursor.execute("SELECT COUNT(*) as count FROM eod_pnl WHERE realized_pnl != 0")
    realized_count = cursor.fetchone()['count']
    
    # Check if unrealized P&L is working  
    cursor.execute("SELECT COUNT(*) as count FROM eod_pnl WHERE unrealized_pnl != 0")
    unrealized_count = cursor.fetchone()['count']
    
    # Check total records
    cursor.execute("SELECT COUNT(*) as count FROM eod_pnl")
    total_count = cursor.fetchone()['count']
    
    print(f"Total EOD records: {total_count}")
    print(f"Records with realized P&L: {realized_count}")
    print(f"Records with unrealized P&L: {unrealized_count}")
    
    if realized_count > 0:
        print("\n✓ REALIZED P&L FIX: SUCCESS")
    else:
        print("\n✗ REALIZED P&L FIX: FAILED")
        
    if unrealized_count > 0:
        print("✓ UNREALIZED P&L: WORKING")
    else:
        print("✗ UNREALIZED P&L: NOT WORKING")
    
    conn.close()

if __name__ == "__main__":
    main() 