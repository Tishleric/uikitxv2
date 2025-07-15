#!/usr/bin/env python
"""Final script to rebuild P&L database with all fixes applied."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.controller import PnLController

def main():
    """Rebuild the P&L database with all fixes."""
    print("P&L DATABASE REBUILD - WITH ALL FIXES")
    print("=" * 60)
    print("\nThis will:")
    print("1. Drop and recreate all P&L tables")
    print("2. Reprocess all trade files") 
    print("3. Reprocess all market price files")
    print("4. Calculate P&L with fixed date handling")
    print("\n" + "=" * 60)
    
    # Create controller
    controller = PnLController()
    
    # Rebuild database
    print("\nRebuilding database...")
    controller.rebuild_database()
    
    print("\nDatabase rebuild complete!")
    print("\nSummary:")
    
    # Show summary
    from lib.trading.pnl_calculator.storage import PnLStorage
    storage = PnLStorage()
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT instrument_name) as positions,
            SUM(realized_pnl) as total_realized,
            SUM(unrealized_pnl) as total_unrealized
        FROM eod_pnl
        WHERE trade_date = (SELECT MAX(trade_date) FROM eod_pnl)
    """)
    
    result = cursor.fetchone()
    if result:
        total_pnl = (result['total_realized'] or 0) + (result['total_unrealized'] or 0)
        print(f"  Total P&L: ${total_pnl:.2f}")
        print(f"  Realized P&L: ${result['total_realized'] or 0:.2f}")
        print(f"  Unrealized P&L: ${result['total_unrealized'] or 0:.2f}")
        print(f"  Active Positions: {result['positions']}")
    
    conn.close()
    
    print("\nYou can now check the P&L Dashboard to verify all values are correct.")

if __name__ == "__main__":
    main() 