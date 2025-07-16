"""
Test Position Tracking System

This script tests the position tracking functionality by:
1. Processing trades with position updates
2. Verifying FIFO P&L calculations
3. Checking position state persistence
4. Testing market price updates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pandas as pd
from datetime import datetime, time
import pytz

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor


def display_position_summary(positions):
    """Display positions in a nice format."""
    if not positions:
        print("No open positions")
        return
    
    print("\nCurrent Positions:")
    print("=" * 120)
    print(f"{'Instrument':<30} {'Position':>10} {'Avg Cost':>10} {'Last Price':>10} {'Realized P&L':>12} {'Unrealized P&L':>12}")
    print("-" * 120)
    
    total_realized = 0
    total_unrealized = 0
    
    for pos in positions:
        total_realized += pos['total_realized_pnl'] or 0
        total_unrealized += pos['unrealized_pnl'] or 0
        
        print(f"{pos['instrument_name']:<30} "
              f"{pos['position_quantity']:>10.0f} "
              f"{pos['avg_cost']:>10.4f} "
              f"{(pos['last_market_price'] or 0):>10.4f} "
              f"${pos['total_realized_pnl']:>11,.2f} "
              f"${pos['unrealized_pnl']:>11,.2f}")
    
    print("-" * 120)
    print(f"{'TOTALS':<30} {'':<10} {'':<10} {'':<10} "
          f"${total_realized:>11,.2f} ${total_unrealized:>11,.2f}")
    print(f"\nTotal P&L: ${total_realized + total_unrealized:,.2f}")


def test_direct_position_manager():
    """Test the position manager directly with sample trades."""
    print("\n" + "="*80)
    print("Testing Direct Position Manager")
    print("="*80)
    
    # Create test database
    test_db = "data/output/test_positions.db"
    storage = PnLStorage(test_db)
    
    # Drop and recreate tables for clean test
    storage.drop_and_recreate_tables()
    
    # Create position manager
    pm = PositionManager(storage)
    
    # Test trades
    test_trades = [
        # Open a futures position
        {
            'instrumentName': 'XCMEFFDPSX20250919U0ZN',
            'marketTradeTime': '2025-07-14 09:00:00',
            'quantity': 10.0,  # Buy 10
            'price': 110.5,
            'tradeId': 'TEST001'
        },
        # Amend position (add more)
        {
            'instrumentName': 'XCMEFFDPSX20250919U0ZN',
            'marketTradeTime': '2025-07-14 10:00:00',
            'quantity': 5.0,  # Buy 5 more
            'price': 110.25,
            'tradeId': 'TEST002'
        },
        # Partial close (realize some P&L)
        {
            'instrumentName': 'XCMEFFDPSX20250919U0ZN',
            'marketTradeTime': '2025-07-14 11:00:00',
            'quantity': -8.0,  # Sell 8
            'price': 110.75,
            'tradeId': 'TEST003'
        },
        # Open an option position
        {
            'instrumentName': 'XCMEOCADPS20250714N0VY2/108.75',
            'marketTradeTime': '2025-07-14 09:30:00',
            'quantity': 20.0,  # Buy 20
            'price': 2.5,
            'tradeId': 'TEST004'
        },
        # SOD trade (midnight)
        {
            'instrumentName': 'XCMEOCADPS20250714N0VY2/108.75',
            'marketTradeTime': '2025-07-14 00:00:00',
            'quantity': -5.0,  # Sell 5 at SOD
            'price': 2.6,
            'tradeId': 'TEST005'
        },
        # Exercised option (zero price)
        {
            'instrumentName': 'XCMEOPADPS20250714N0VY2/111.25',
            'marketTradeTime': '2025-07-14 12:00:00',
            'quantity': 10.0,
            'price': 0.0,  # Exercise
            'tradeId': 'TEST006'
        }
    ]
    
    # Process each trade
    for trade in test_trades:
        print(f"\nProcessing: {trade['instrumentName']} {trade['quantity']:+.0f} @ {trade['price']}")
        
        update = pm.process_trade(trade)
        
        print(f"  Action: {update.trade_action}")
        print(f"  Position: {update.previous_quantity:.0f} → {update.new_quantity:.0f}")
        print(f"  Realized P&L: ${update.realized_pnl:,.2f}")
        if update.is_sod:
            print("  ⚠️  SOD Trade")
        if update.is_exercised:
            print("  ⚠️  EXERCISED Option")
    
    # Display current positions
    positions = pm.get_positions()
    display_position_summary(positions)
    
    # Test market price update
    print("\n\nUpdating market prices...")
    
    # Simulate market prices by manually inserting some
    # In real usage, this would come from price files
    chicago_tz = pytz.timezone('America/Chicago')
    price_time = datetime.now(chicago_tz).replace(hour=14, minute=0)  # 2pm CDT
    
    # For testing, directly update prices
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Update futures price
    cursor.execute("""
        UPDATE positions 
        SET last_market_price = 111.0, 
            unrealized_pnl = (111.0 - avg_cost) * position_quantity,
            last_updated = ?
        WHERE instrument_name = 'XCMEFFDPSX20250919U0ZN'
    """, (price_time,))
    
    # Update option price
    cursor.execute("""
        UPDATE positions 
        SET last_market_price = 2.7,
            unrealized_pnl = (2.7 - avg_cost) * position_quantity,
            last_updated = ?
        WHERE instrument_name = 'XCMEOCADPS20250714N0VY2/108.75'
    """, (price_time,))
    
    conn.commit()
    conn.close()
    
    # Display updated positions
    positions = pm.get_positions()
    display_position_summary(positions)
    
    # Test snapshots
    print("\n\nTaking position snapshots...")
    
    # Take EOD snapshot (4pm)
    eod_time = datetime.now(chicago_tz).replace(hour=16, minute=0, second=0)
    pm.take_snapshot('EOD', eod_time)
    print(f"✓ EOD snapshot taken at {eod_time}")
    
    # Take SOD snapshot (5pm)
    sod_time = datetime.now(chicago_tz).replace(hour=17, minute=0, second=0)
    pm.take_snapshot('SOD', sod_time)
    print(f"✓ SOD snapshot taken at {sod_time}")


def test_with_real_trades():
    """Test position tracking with real trade files."""
    print("\n\n" + "="*80)
    print("Testing with Real Trade Files")
    print("="*80)
    
    # Create test database
    test_db = "data/output/test_positions_real.db"
    storage = PnLStorage(test_db)
    
    # Drop and recreate tables
    storage.drop_and_recreate_tables()
    
    # Create preprocessor with position tracking enabled
    preprocessor = TradePreprocessor(
        output_dir="data/output/test_preprocessor_positions",
        enable_position_tracking=True,
        storage=storage
    )
    
    # Find trade files
    trade_dir = Path("data/input/trade_ledger")
    trade_files = sorted(trade_dir.glob("trades_*.csv"))
    
    if not trade_files:
        print("No trade files found")
        return
    
    # Process each file
    for trade_file in trade_files:
        print(f"\nProcessing: {trade_file.name}")
        result = preprocessor.process_trade_file(str(trade_file))
        
        if result is not None:
            # Show position actions from the trades
            if 'position_action' in result.columns:
                actions = result[result['position_action'].notna()]['position_action'].value_counts()
                print(f"  Position actions: {actions.to_dict()}")
                
                # Show realized P&L
                if 'realized_pnl' in result.columns:
                    total_realized = result['realized_pnl'].sum()
                    print(f"  Total realized P&L: ${total_realized:,.2f}")
    
    # Display final positions
    positions = preprocessor.position_manager.get_positions()
    display_position_summary(positions)
    
    # Check for special cases
    print("\n\nSpecial Cases Detected:")
    for pos in positions:
        if pos['has_exercised_trades']:
            print(f"  ⚠️  {pos['instrument_name']} has exercised trades")
        if pos['is_option']:
            print(f"  📊 {pos['instrument_name']} is an option (strike: {pos['option_strike']}, expiry: {pos['option_expiry']})")


def main():
    """Run all tests."""
    print("Position Tracking System Test")
    print("=" * 80)
    
    # Test 1: Direct position manager with synthetic trades
    test_direct_position_manager()
    
    # Test 2: Real trade files
    test_with_real_trades()
    
    print("\n\nAll tests complete!")


if __name__ == "__main__":
    main() 