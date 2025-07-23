#!/usr/bin/env python3
"""Manually calculate and store EOD P&L snapshot."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date
import pytz
from lib.trading.pnl_integration.eod_snapshot_service import EODSnapshotService

CHICAGO_TZ = pytz.timezone('America/Chicago')

def main():
    print("Manual EOD Snapshot Calculation")
    print("=" * 50)
    
    # Create service
    service = EODSnapshotService()
    
    # Get current date
    now = datetime.now(CHICAGO_TZ)
    pnl_date = now.date()
    
    print(f"Calculating EOD P&L for: {pnl_date}")
    print(f"Current Chicago time: {now}")
    
    try:
        # Calculate P&L using the SQL-based method
        print("\nCalculating settlement-aware P&L...")
        pnl_df = service.calculate_settlement_aware_pnl_with_fifo(pnl_date)
        
        if pnl_df.empty:
            print("\n❌ No P&L data calculated")
            print("This could mean:")
            print("  - No trades in the period")
            print("  - No P&L components with matching settlement keys")
            print("  - No open lot snapshots available")
        else:
            print(f"\n✅ P&L calculated for {len(pnl_df)} symbols:")
            print("\nP&L Summary:")
            print("-" * 60)
            print(f"{'Symbol':<10} {'Realized':<12} {'Unrealized':<12} {'Total Daily':<12}")
            print("-" * 60)
            
            total_realized = 0
            total_unrealized = 0
            total_daily = 0
            
            for _, row in pnl_df.iterrows():
                print(f"{row['symbol']:<10} "
                      f"${row.get('realized_pnl', 0):>10,.2f} "
                      f"${row.get('unrealized_pnl', 0):>10,.2f} "
                      f"${row.get('total_daily_pnl', 0):>10,.2f}")
                
                total_realized += row.get('realized_pnl', 0)
                total_unrealized += row.get('unrealized_pnl', 0)
                total_daily += row.get('total_daily_pnl', 0)
            
            print("-" * 60)
            print(f"{'TOTAL':<10} "
                  f"${total_realized:>10,.2f} "
                  f"${total_unrealized:>10,.2f} "
                  f"${total_daily:>10,.2f}")
            
            # Write to history
            print("\n\nWriting snapshot to history...")
            success = service.write_snapshot_to_history(pnl_df, pnl_date)
            
            if success:
                print("✅ EOD snapshot successfully written to tyu5_eod_pnl_history")
            else:
                print("❌ Failed to write EOD snapshot")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 