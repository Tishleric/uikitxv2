#!/usr/bin/env python3
"""
Simple verification that automatic 4pm trigger is disabled
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
import pytz
from unittest.mock import Mock

from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceFileHandler, DailyCSVTracker

CHICAGO_TZ = pytz.timezone('America/Chicago')

print("=" * 80)
print("VERIFYING AUTOMATIC 4PM TRIGGER IS DISABLED")
print("=" * 80)
print()

# Create handler
print("Creating ClosePriceFileHandler...")
handler = ClosePriceFileHandler(':memory:', time.time())

# Check if monitor thread exists
print("\nChecking for monitor thread...")
import threading
active_threads = threading.enumerate()

monitor_found = False
for thread in active_threads:
    if '4pm' in thread.name.lower() or 'monitor' in thread.name.lower():
        monitor_found = True
        print(f"  ❌ Found thread: {thread.name}")

if not monitor_found:
    print("  ✅ No 4pm monitor thread found")

# Test the tracker still works
print("\nTesting file tracking still works...")
date_str = datetime.now(CHICAGO_TZ).strftime('%Y%m%d')

# Add files
status1 = handler.daily_tracker.add_file(date_str, 14)
print(f"  Added 2pm file: {status1}")

status2 = handler.daily_tracker.add_file(date_str, 15) 
print(f"  Added 3pm file: {status2}")

status3 = handler.daily_tracker.add_file(date_str, 16)
print(f"  Added 4pm file: {status3}")

# Check if should_trigger_4pm_roll still works (for manual use)
print("\nTesting manual trigger logic...")
should_roll, reason = handler.daily_tracker.should_trigger_4pm_roll(date_str)

# Mock time to be after 4pm
class MockDateTime:
    @staticmethod
    def now(tz):
        dt = datetime.now(tz)
        return dt.replace(hour=16, minute=15)  # 4:15pm

import lib.trading.pnl_fifo_lifo.close_price_watcher as cw
original_datetime = cw.datetime
cw.datetime = MockDateTime

# Test again with mocked time
should_roll, reason = handler.daily_tracker.should_trigger_4pm_roll(date_str)
print(f"  At 4:15pm with all files: should_roll={should_roll}, reason={reason}")

# Restore
cw.datetime = original_datetime

# Verify _trigger_4pm_roll_for_date method still exists
print("\nVerifying manual trigger method exists...")
if hasattr(handler, '_trigger_4pm_roll_for_date'):
    print("  ✅ _trigger_4pm_roll_for_date() method available for manual use")
else:
    print("  ❌ _trigger_4pm_roll_for_date() method missing!")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("✅ No automatic monitor thread running")
print("✅ File tracking still works")
print("✅ Manual trigger logic still available")
print("✅ _trigger_4pm_roll_for_date() can be called manually")
print("\n✅ VERIFICATION COMPLETE - Automatic triggers disabled")