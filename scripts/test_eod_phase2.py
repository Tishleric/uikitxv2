#!/usr/bin/env python3
"""
Test script to verify Phase 2 EOD P&L implementation.

This script tests:
1. Market price monitor functionality
2. EOD service integration with TYU5
3. Manual EOD calculation
"""

import sys
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.market_price_monitor import MarketPriceMonitor
from lib.trading.pnl_integration.eod_snapshot_service import EODSnapshotService
from lib.trading.pnl_integration.settlement_constants import CHICAGO_TZ


def test_market_price_monitor():
    """Test market price monitoring functionality."""
    print("1. Testing Market Price Monitor...")
    
    monitor = MarketPriceMonitor()
    
    # Test batch detection
    batch_started = monitor.detect_4pm_batch_start()
    print(f"   4pm batch started: {batch_started}")
    
    if batch_started:
        # Track updates
        status = monitor.track_symbol_updates()
        stats = monitor.get_completion_stats()
        
        print(f"   Total symbols: {stats['total_symbols']}")
        print(f"   Updated: {stats['updated_symbols']}")
        print(f"   Pending: {stats['pending_symbols']}")
        print(f"   Completion: {stats['completion_ratio']:.1%}")
        print(f"   Is complete: {stats['is_complete']}")
        
        if stats['missing_symbols']:
            print(f"   First missing: {', '.join(stats['missing_symbols'][:5])}")
    else:
        print("   No recent 4pm updates detected")


def test_tyu5_integration():
    """Test TYU5 integration."""
    print("\n2. Testing TYU5 Integration...")
    
    # Check if TYU5 tables exist
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for TYU5 positions
    cursor.execute("""
        SELECT COUNT(*) FROM tyu5_positions
        WHERE Net_Quantity != 0
    """)
    position_count = cursor.fetchone()[0]
    print(f"   Active positions in TYU5: {position_count}")
    
    # Check for FIFO breakdown
    cursor.execute("""
        SELECT COUNT(*) FROM tyu5_position_breakdown
    """)
    lot_count = cursor.fetchone()[0]
    print(f"   FIFO lots in breakdown: {lot_count}")
    
    # Check latest calculation
    cursor.execute("""
        SELECT MAX(timestamp) FROM tyu5_runs
    """)
    latest_run = cursor.fetchone()[0]
    if latest_run:
        print(f"   Latest TYU5 run: {latest_run}")
    else:
        print("   No TYU5 runs found")
    
    conn.close()


async def test_manual_eod_calculation():
    """Test manual EOD calculation."""
    print("\n3. Testing Manual EOD Calculation...")
    
    service = EODSnapshotService()
    
    # Get latest available price date
    latest_date = service._get_latest_price_date()
    if not latest_date:
        print("   ✗ No price data available")
        return
    
    print(f"   Latest price date: {latest_date}")
    
    # Check if we already have EOD for this date
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM tyu5_eod_pnl_history
        WHERE snapshot_date = ?
    """, (latest_date.isoformat(),))
    
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        print(f"   EOD already exists for {latest_date} ({existing_count} records)")
        
        # Show TOTAL row
        cursor.execute("""
            SELECT * FROM tyu5_eod_pnl_history
            WHERE snapshot_date = ? AND symbol = 'TOTAL'
        """, (latest_date.isoformat(),))
        
        total_row = cursor.fetchone()
        if total_row:
            print(f"\n   TOTAL P&L Summary:")
            print(f"   Realized: ${total_row[4]:,.2f}")
            print(f"   Unrealized (settle): ${total_row[5]:,.2f}")
            print(f"   Unrealized (current): ${total_row[6]:,.2f}")
            print(f"   Total Daily P&L: ${total_row[7]:,.2f}")
    else:
        print(f"   No EOD snapshot for {latest_date}")
        print("   Running manual calculation...")
        
        # Run calculation
        success = await service.trigger_eod_snapshot(latest_date)
        
        if success:
            print("   ✓ EOD calculation completed")
            
            # Show results
            cursor.execute("""
                SELECT COUNT(*) FROM tyu5_eod_pnl_history
                WHERE snapshot_date = ? AND symbol != 'TOTAL'
            """, (latest_date.isoformat(),))
            
            position_count = cursor.fetchone()[0]
            print(f"   Created {position_count} position snapshots")
        else:
            print("   ✗ EOD calculation failed")
    
    conn.close()


def test_eod_history_views():
    """Test EOD history views."""
    print("\n4. Testing EOD History Views...")
    
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    
    # Test daily totals view
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tyu5_daily_pnl_totals
        ORDER BY snapshot_date DESC
        LIMIT 5
    """)
    
    totals = cursor.fetchall()
    if totals:
        print("   Recent daily totals:")
        for row in totals:
            date = row[0]
            total_pnl = row[7]
            print(f"   {date}: ${total_pnl:,.2f}")
    else:
        print("   No daily totals available")
    
    # Test latest snapshot view
    cursor.execute("""
        SELECT COUNT(*) FROM tyu5_latest_eod_snapshot
    """)
    
    snapshot_count = cursor.fetchone()[0]
    print(f"\n   Latest snapshot has {snapshot_count} positions")
    
    conn.close()


async def main():
    """Run all Phase 2 tests."""
    print("=" * 60)
    print("EOD P&L Phase 2 Verification")
    print("=" * 60)
    
    test_market_price_monitor()
    test_tyu5_integration()
    await test_manual_eod_calculation()
    test_eod_history_views()
    
    print("\n" + "=" * 60)
    print("Phase 2 verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main()) 