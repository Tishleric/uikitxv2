#!/usr/bin/env python3
"""
Test script to verify Phase 1 EOD P&L implementation.

This script tests:
1. Database table creation
2. Settlement time calculations
3. EOD service initialization
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, date, time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.settlement_constants import (
    CHICAGO_TZ, SETTLEMENT_TIME, EOD_TIME,
    get_settlement_boundaries, get_eod_boundary,
    split_position_at_settlement
)
from lib.trading.pnl_integration.eod_snapshot_service import EODSnapshotService


def test_table_exists():
    """Verify EOD history table was created."""
    print("1. Testing EOD History Table...")
    
    db_path = "data/output/pnl/pnl_tracker.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tyu5_eod_pnl_history'
    """)
    
    result = cursor.fetchone()
    if result:
        print("   ✓ Table tyu5_eod_pnl_history exists")
        
        # Check columns
        cursor.execute("PRAGMA table_info(tyu5_eod_pnl_history)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   ✓ Columns: {', '.join(columns)}")
    else:
        print("   ✗ Table NOT found!")
    
    conn.close()


def test_settlement_calculations():
    """Test settlement boundary calculations."""
    print("\n2. Testing Settlement Calculations...")
    
    test_date = date(2025, 7, 22)
    
    # Get boundaries
    prev_4pm, curr_2pm = get_settlement_boundaries(test_date)
    curr_4pm = get_eod_boundary(test_date)
    
    print(f"   Trading date: {test_date}")
    print(f"   Previous 4pm: {prev_4pm.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"   Settlement (2pm): {curr_2pm.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"   Current 4pm: {curr_4pm.strftime('%Y-%m-%d %H:%M %Z')}")
    
    # Test position splitting
    print("\n   Testing position split for 11am entry:")
    entry_time = CHICAGO_TZ.localize(datetime.combine(test_date, time(11, 0)))
    exit_time = curr_4pm
    
    segments = split_position_at_settlement(entry_time, exit_time, test_date)
    
    for i, (start, end, seg_type) in enumerate(segments):
        print(f"   Segment {i+1}: {start.strftime('%H:%M')} → {end.strftime('%H:%M')} ({seg_type})")


def test_eod_service():
    """Test EOD service initialization."""
    print("\n3. Testing EOD Service...")
    
    try:
        service = EODSnapshotService()
        print("   ✓ Service initialized successfully")
        
        # Test market price detection
        has_updates = service.detect_4pm_update_completion()
        print(f"   ✓ Market price detection: {'Updates found' if has_updates else 'No recent updates'}")
        
        # Test latest price date
        latest_date = service._get_latest_price_date()
        if latest_date:
            print(f"   ✓ Latest price date: {latest_date}")
        else:
            print("   - No price data available yet")
            
    except Exception as e:
        print(f"   ✗ Service error: {e}")


def test_sample_pnl_calculation():
    """Test sample P&L calculation with settlement split."""
    print("\n4. Sample P&L Calculation (11am entry → 4pm):")
    
    # Example values
    entry_price = 110.0
    px_settle = 111.0  # 2pm settlement
    current_price = 112.0  # 4pm price
    quantity = 10
    multiplier = 1000
    
    # Calculate P&L segments
    pnl_to_settlement = quantity * (px_settle - entry_price) * multiplier
    pnl_from_settlement = quantity * (current_price - px_settle) * multiplier
    total_pnl = pnl_to_settlement + pnl_from_settlement
    
    print(f"   Entry: 11am @ ${entry_price}")
    print(f"   Settlement: 2pm @ ${px_settle}")
    print(f"   Current: 4pm @ ${current_price}")
    print(f"   Position: {quantity} contracts")
    print(f"\n   P&L Calculation:")
    print(f"   11am → 2pm: ({px_settle} - {entry_price}) × {quantity} × {multiplier} = ${pnl_to_settlement:,.2f}")
    print(f"   2pm → 4pm: ({current_price} - {px_settle}) × {quantity} × {multiplier} = ${pnl_from_settlement:,.2f}")
    print(f"   Total P&L: ${total_pnl:,.2f}")


def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("EOD P&L Phase 1 Verification")
    print("=" * 60)
    
    test_table_exists()
    test_settlement_calculations()
    test_eod_service()
    test_sample_pnl_calculation()
    
    print("\n" + "=" * 60)
    print("Phase 1 verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main() 