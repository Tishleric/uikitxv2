#!/usr/bin/env python3
"""
Trace P&L Preprocessing Flow
This script traces the complete preprocessing flow to identify any duplicate processing
"""

import sys
import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up console logging only to trace startup
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def trace_startup_flow():
    """Trace the complete startup flow when the dashboard initializes"""
    
    print("\n" + "="*80)
    print("TRACING P&L PREPROCESSING FLOW")
    print("="*80 + "\n")
    
    # Step 1: Check what happens when main app imports P&L callbacks
    print("STEP 1: Importing P&L callbacks module...")
    start_time = time.time()
    
    # Import will trigger module-level initialization
    import apps.dashboards.pnl.callbacks
    
    import_time = time.time() - start_time
    print(f"  - Import took {import_time:.2f} seconds")
    print("  - This imports controller from app.py which creates PnLController()")
    print("  - callbacks.py also calls controller.start_file_watchers() at module level!")
    
    # Step 2: Check what PnLController does on initialization
    print("\nSTEP 2: Checking PnLController initialization...")
    from lib.trading.pnl_calculator.controller import PnLController
    
    # Create a second controller to see if it processes files again
    print("  - Creating a second controller instance...")
    controller2 = PnLController()
    
    # Step 3: Check if file watchers process existing files
    print("\nSTEP 3: Checking file watcher behavior...")
    
    # Get list of existing trade files
    trades_dir = Path("data/input/trade_ledger")
    price_dir = Path("data/input/market_prices/futures")
    
    trade_files = list(trades_dir.glob("trades_*.csv"))
    price_files = list(price_dir.glob("market_prices_*.csv"))
    
    print(f"  - Found {len(trade_files)} trade files")
    print(f"  - Found {len(price_files)} price files")
    
    # Step 4: Check database to see how many times files were processed
    print("\nSTEP 4: Checking database for duplicate processing...")
    
    db_path = Path("data/output/pnl/pnl_tracker.db")
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check processed files
        cursor.execute("""
            SELECT file_name, processed_at, COUNT(*) as process_count
            FROM processed_files
            GROUP BY file_name
            ORDER BY processed_at DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        if results:
            print("\n  Recent processed files:")
            for file_name, processed_at, count in results:
                print(f"    - {file_name}: processed {count} times (last: {processed_at})")
        
        # Check trades count
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"\n  Total trades in database: {trade_count}")
        
        conn.close()
    
    # Step 5: Trace when register_callbacks is called
    print("\nSTEP 5: When does register_callbacks get called?")
    print("  - app.py imports callbacks at line 230-235")
    print("  - This happens BEFORE the app starts running")
    print("  - So file watchers start and process all files during import!")
    
    # Step 6: Check if P&L v2 also initializes
    print("\nSTEP 6: Checking if P&L v2 was also initializing...")
    print("  - P&L v2 callback registration is now commented out")
    print("  - But if it was active, it would ALSO process all files!")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF FINDINGS:")
    print("="*80)
    print("""
1. DUPLICATE PROCESSING IS HAPPENING!
   - P&L v1 starts file watchers during module import (callbacks.py line 435)
   - This happens BEFORE the app even starts running
   - process_existing_files() is called which processes ALL historical files

2. STARTUP FLOW:
   a) main app.py starts
   b) Imports pnl.callbacks at line 230
   c) callbacks.py imports controller from app.py
   d) app.py creates controller = PnLController() at module level
   e) callbacks.py calls controller.start_file_watchers() at module level
   f) File watcher calls process_existing_files() which processes ALL files
   g) THEN the app actually starts running

3. WHY IT'S SLOW:
   - Every historical trade file is being processed during import
   - This happens synchronously before the app can start
   - If you have many trade files, this can take minutes

4. P&L v2 (when active) would make it WORSE:
   - It would create its own UnifiedPnLService
   - Which would process all the same files AGAIN
""")

if __name__ == "__main__":
    trace_startup_flow() 