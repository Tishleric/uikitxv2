#!/usr/bin/env python3
"""
Reset all market prices and processing history for comprehensive testing.
This script carefully empties tables and clears processing state files.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import shutil

print("=" * 70)
print("COMPREHENSIVE DATA RESET FOR TESTING")
print("=" * 70)
print("\nThis script will:")
print("1. Empty all market price tables (preserving schema)")
print("2. Clear all processing history files")
print("3. Empty P&L tracking tables (preserving schema)")
print("\n⚠️  WARNING: This will delete all data but preserve table structures")

response = input("\nAre you sure you want to proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Operation cancelled.")
    exit()

# Backup directory
backup_dir = Path(f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup_dir.mkdir(exist_ok=True)
print(f"\nCreating backups in: {backup_dir}")

# === SECTION 1: Market Prices Database ===
print("\n" + "=" * 50)
print("SECTION 1: Market Prices Database")
print("=" * 50)

market_db_path = Path("data/output/market_prices/market_prices.db")
if market_db_path.exists():
    # Backup first
    shutil.copy2(market_db_path, backup_dir / "market_prices.db")
    print(f"✓ Backed up market_prices.db")
    
    conn = sqlite3.connect(str(market_db_path))
    cursor = conn.cursor()
    
    # Tables to empty
    tables = ['futures_prices', 'options_prices', 'price_history', 'price_file_tracker']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✓ Emptied {table} ({count} rows deleted)")
            else:
                print(f"  - {table} was already empty")
        except sqlite3.OperationalError:
            print(f"  ⚠️  Table {table} does not exist")
    
    conn.commit()
    conn.close()
else:
    print("⚠️  Market prices database not found")

# === SECTION 2: P&L Tracker Database ===
print("\n" + "=" * 50)
print("SECTION 2: P&L Tracker Database")
print("=" * 50)

pnl_db_path = Path("data/output/pnl/pnl_tracker.db")
if pnl_db_path.exists():
    # Backup first
    shutil.copy2(pnl_db_path, backup_dir / "pnl_tracker.db")
    print(f"✓ Backed up pnl_tracker.db")
    
    conn = sqlite3.connect(str(pnl_db_path))
    cursor = conn.cursor()
    
    # Tables to empty (only TYU5 and related tables)
    tables = [
        'tyu5_trades', 'tyu5_positions', 'tyu5_summary', 
        'tyu5_risk_matrix', 'tyu5_position_breakdown',
        'tyu5_pnl_components', 'tyu5_open_lot_snapshots',
        'tyu5_eod_pnl_history', 'tyu5_runs', 'tyu5_alerts',
        'FULLPNL'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✓ Emptied {table} ({count} rows deleted)")
            else:
                print(f"  - {table} was already empty")
        except sqlite3.OperationalError:
            print(f"  ⚠️  Table {table} does not exist")
    
    conn.commit()
    conn.close()
else:
    print("⚠️  P&L tracker database not found")

# === SECTION 2.5: Actant EOD Database ===
print("\n" + "=" * 50)
print("SECTION 2.5: Actant EOD Database")
print("=" * 50)

actant_db_path = Path("data/output/eod/actant_eod_data.db")
if actant_db_path.exists():
    # Backup first
    shutil.copy2(actant_db_path, backup_dir / "actant_eod_data.db")
    print(f"✓ Backed up actant_eod_data.db")
    
    conn = sqlite3.connect(str(actant_db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✓ Emptied {table} ({count} rows deleted)")
            else:
                print(f"  - {table} was already empty")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️  Error with table {table}: {e}")
    
    conn.commit()
    conn.close()
else:
    print("⚠️  Actant EOD database not found")

# === SECTION 3: Processing History Files ===
print("\n" + "=" * 50)
print("SECTION 3: Processing History Files")
print("=" * 50)

# List of processing history files to clear
history_files = [
    # Trade processing state
    ("data/output/trade_ledger_processed/.processing_state.json", "Trade processing state"),
    
    # P&L processing history
    ("data/output/pnl/processing_history.json", "P&L processing history"),
    
    # Market price watcher states (if any exist)
    ("data/output/market_prices/.processing_state.json", "Market price processing state"),
    
    # Spot risk processing state
    ("data/output/spot_risk/.processing_state.json", "Spot risk processing state"),
    
    # Spot risk file watcher state
    ("data/output/spot_risk/.file_watcher_state.json", "Spot risk file watcher state"),
]

for file_path, description in history_files:
    path = Path(file_path)
    if path.exists():
        # Backup
        backup_name = path.name
        shutil.copy2(path, backup_dir / backup_name)
        
        # Clear by writing empty JSON
        with open(path, 'w') as f:
            json.dump({}, f)
        print(f"  ✓ Cleared {description}: {file_path}")
    else:
        print(f"  - {description} not found: {file_path}")

# === SECTION 4: Other Cleanup ===
print("\n" + "=" * 50)
print("SECTION 4: Other Cleanup")
print("=" * 50)

# Clear any temporary files
temp_patterns = [
    "data/output/pnl/*.xlsx",  # Excel files
    "data/output/pnl/tyu5_debug_*.xlsx",  # Debug Excel files
]

for pattern in temp_patterns:
    files = list(Path(".").glob(pattern))
    if files:
        for f in files:
            print(f"  ✓ Deleted temporary file: {f}")
            f.unlink()
    else:
        print(f"  - No files matching: {pattern}")

# === SUMMARY ===
print("\n" + "=" * 70)
print("RESET COMPLETE")
print("=" * 70)
print(f"\n✓ All data has been cleared")
print(f"✓ Backups saved to: {backup_dir}")
print("\nYou can now run the watchers for a clean test:")
print("  > run_all_watchers.bat")
print("\nTo restore from backup, copy files from:")
print(f"  {backup_dir}") 