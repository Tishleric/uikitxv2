#!/usr/bin/env python
"""Safely rerun TYU5 with database backups."""

import sys
import shutil
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def backup_database(db_path):
    """Create a backup of the database."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    return backup_path

def analyze_before_after(db_path):
    """Analyze lot_positions before and after."""
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT symbol, COUNT(*) as lot_count, SUM(remaining_quantity) as total_qty
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    """Safely rerun TYU5 with our fixes."""
    
    print("=" * 80)
    print("SAFE TYU5 RERUN WITH DATABASE BACKUP")
    print("=" * 80)
    
    db_path = "data/output/pnl/pnl_tracker.db"
    
    # 1. Backup database
    print("\n1. Creating database backup...")
    backup_path = backup_database(db_path)
    
    # 2. Show current state
    print("\n2. Current lot_positions state:")
    print("-" * 60)
    before_df = analyze_before_after(db_path)
    print(before_df)
    print(f"\nTotal symbols with lots: {len(before_df)}")
    
    # 3. Clear Python module cache by starting fresh
    print("\n3. Starting fresh Python process to clear module cache...")
    print("-" * 60)
    
    # Create a temporary script that imports and runs TYU5 fresh
    temp_script = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import TYU5 service fresh
from lib.trading.pnl_integration.tyu5_service import TYU5Service

# Run with database writer enabled
print("Running TYU5 with database writer enabled...")
service = TYU5Service(enable_attribution=False, enable_db_writer=True)

try:
    output_file = service.calculate_pnl(output_format="excel")
    print(f"✓ TYU5 calculation complete: {output_file}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
"""
    
    temp_file = "scripts/temp_tyu5_run.py"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(temp_script)
    
    # Run in a fresh Python process
    import subprocess
    result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Clean up temp file
    Path(temp_file).unlink()
    
    # 4. Show after state
    print("\n4. After lot_positions state:")
    print("-" * 60)
    after_df = analyze_before_after(db_path)
    print(after_df)
    print(f"\nTotal symbols with lots: {len(after_df)}")
    
    # 5. Summary
    print("\n5. SUMMARY")
    print("-" * 60)
    print(f"Before: {len(before_df)} symbols with lot tracking")
    print(f"After: {len(after_df)} symbols with lot tracking")
    
    if len(after_df) > len(before_df):
        print("\n✓ SUCCESS: Lot tracking coverage improved!")
        print(f"  Added {len(after_df) - len(before_df)} new symbols")
    elif len(after_df) == len(before_df):
        print("\n⚠ No change in coverage")
        print("  The fixes may still be cached. Try:")
        print("  1. Close all Python processes")
        print("  2. Open a new terminal")
        print("  3. Run this script again")
    
    print(f"\n✓ Database backup saved at: {backup_path}")
    print("  To restore: copy backup file back to original name")

if __name__ == "__main__":
    main() 