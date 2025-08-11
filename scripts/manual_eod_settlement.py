#!/usr/bin/env python3
"""
Manual trigger for 4pm roll and EOD settlement
Replaces automatic monitoring with operator-controlled process
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import sqlite3
from datetime import datetime
import pytz
from pathlib import Path

from lib.trading.pnl_fifo_lifo.data_manager import roll_4pm_prices, perform_eod_settlement

# Chicago timezone
CHICAGO_TZ = pytz.timezone('America/Chicago')


def get_file_status(date_str):
    """Check which close price files have been received"""
    # Expected directories from config
    futures_dir = Path(r'Z:\Trade_Control\Futures')
    options_dir = Path(r'Z:\Trade_Control\Options')
    
    received_files = {}
    
    # Check futures files
    for hour in [14, 15, 16]:
        futures_file = futures_dir / f'Futures_{date_str}_{hour:02d}00.csv'
        options_file = options_dir / f'Options_{date_str}_{hour:02d}00.csv'
        
        if futures_file.exists() and options_file.exists():
            received_files[hour] = 'Both'
        elif futures_file.exists():
            received_files[hour] = 'Futures only'
        elif options_file.exists():
            received_files[hour] = 'Options only'
        else:
            received_files[hour] = 'Missing'
    
    return received_files


def check_already_triggered(conn, date_str):
    """Check if 4pm roll was already triggered today"""
    cursor = conn.cursor()
    
    # Check if sodTod prices exist with today's date
    # This indicates 4pm roll already happened
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pricing 
        WHERE price_type = 'sodTod' 
        AND DATE(timestamp) = DATE(?)
    """, (f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}',))
    
    count = cursor.fetchone()[0]
    return count > 0


def trigger_4pm_roll(conn, date_str):
    """Execute the 4pm roll and EOD settlement"""
    cursor = conn.cursor()
    
    # Get all unique symbols from pricing table
    cursor.execute("SELECT DISTINCT symbol FROM pricing WHERE symbol LIKE '% Comdty'")
    symbols = [row[0] for row in cursor.fetchall()]
    
    if not symbols:
        print("ERROR: No symbols found in pricing table")
        return False
    
    print(f"\nFound {len(symbols)} symbols to process")
    
    # Build close prices dict for EOD settlement
    close_prices = {}
    for symbol in symbols:
        cursor.execute("SELECT price FROM pricing WHERE symbol = ? AND price_type = 'close'", (symbol,))
        result = cursor.fetchone()
        if result:
            close_prices[symbol] = result[0]
    
    print(f"Found close prices for {len(close_prices)} symbols")
    
    # Roll prices for each symbol
    print("\nExecuting 4pm price roll...")
    for i, symbol in enumerate(symbols):
        if i % 10 == 0:  # Progress indicator
            print(f"  Processing {i+1}/{len(symbols)} symbols...")
        roll_4pm_prices(conn, symbol)
    
    # Perform EOD settlement (mark-to-market)
    settlement_date = datetime.strptime(date_str, '%Y%m%d').date()
    print(f"\nPerforming EOD settlement for {settlement_date}...")
    perform_eod_settlement(conn, settlement_date, close_prices)
    
    conn.commit()
    print(f"\n✅ Successfully completed 4pm roll and EOD settlement for {len(symbols)} symbols")
    return True


def main():
    parser = argparse.ArgumentParser(description='Manual 4pm EOD Settlement Trigger')
    parser.add_argument('--date', help='Date in YYYYMMDD format (default: today)')
    parser.add_argument('--db', default='trades.db', help='Path to trades database')
    parser.add_argument('--force', action='store_true', help='Force execution without all files')
    
    args = parser.parse_args()
    
    # Get date
    if args.date:
        date_str = args.date
        date_obj = datetime.strptime(date_str, '%Y%m%d')
    else:
        date_obj = datetime.now(CHICAGO_TZ)
        date_str = date_obj.strftime('%Y%m%d')
    
    print("=" * 80)
    print("MANUAL 4PM EOD SETTLEMENT TRIGGER")
    print("=" * 80)
    print(f"Date: {date_str}")
    print(f"Database: {args.db}")
    print(f"Current Chicago time: {datetime.now(CHICAGO_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check file status
    print("Checking file status...")
    file_status = get_file_status(date_str)
    
    print("\nFile Status:")
    print("-" * 40)
    all_received = True
    for hour in [14, 15, 16]:
        status = file_status.get(hour, 'Missing')
        marker = "✅" if status == 'Both' else "⚠️"
        print(f"{marker} {hour}:00 ({hour-12}pm): {status}")
        if status != 'Both':
            all_received = False
    
    # Connect to database
    conn = sqlite3.connect(args.db)
    
    try:
        # Check if already triggered
        if check_already_triggered(conn, date_str):
            print("\n❌ ERROR: 4pm roll already triggered for this date")
            print("   (sodTod prices already exist)")
            return 1
        
        # Check time
        now_chicago = datetime.now(CHICAGO_TZ)
        current_hour = now_chicago.hour + now_chicago.minute / 60.0
        
        print(f"\nCurrent time check: {now_chicago.strftime('%H:%M')} Chicago time")
        
        # Apply production logic
        can_trigger = False
        reason = ""
        
        if all_received and current_hour >= 16.0:
            can_trigger = True
            reason = "All files received and past 4pm"
        elif current_hour >= 16.5 and file_status.get(16) == 'Both':
            can_trigger = True
            reason = "Past 4:30pm and 4pm file received"
        elif args.force:
            can_trigger = True
            reason = "Forced execution"
        else:
            if not all_received:
                reason = "Not all files received"
            elif current_hour < 16.0:
                reason = "Not yet 4pm CDT"
            else:
                reason = "Conditions not met"
        
        if not can_trigger:
            print(f"\n❌ Cannot trigger: {reason}")
            if not args.force:
                print("\n   Use --force to override safety checks")
            return 1
        
        # Confirm execution
        print(f"\n✅ Ready to trigger 4pm roll")
        print(f"   Reason: {reason}")
        print("\nThis will:")
        print("  1. Move sodTom → sodTod prices")
        print("  2. Clear sodTom prices")
        print("  3. Mark all open positions to settlement price")
        print("  4. Calculate unrealized P&L")
        
        response = input("\nProceed? (yes/no): ")
        
        if response.lower() != 'yes':
            print("\nCancelled by user")
            return 0
        
        # Execute
        success = trigger_4pm_roll(conn, date_str)
        
        if success:
            print("\n✅ EOD settlement completed successfully")
            return 0
        else:
            print("\n❌ EOD settlement failed")
            return 1
            
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())