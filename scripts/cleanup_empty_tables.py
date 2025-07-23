#!/usr/bin/env python3
"""
Safe cleanup script for empty tables in pnl_tracker.db.

This script only removes tables that are:
1. Empty (0 rows)
2. Part of the legacy P&L calculator system (replaced by TYU5)
3. Not referenced by the current TYU5 system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from datetime import datetime

def main():
    """Clean up empty legacy tables."""
    db_path = 'data/output/pnl/pnl_tracker.db'
    
    # Tables that are safe to remove - legacy P&L calculator tables
    # that have been replaced by TYU5 equivalents
    legacy_tables_to_remove = [
        'file_processing_log',     # Replaced by tyu5_runs tracking
        'pnl_audit_log',          # Replaced by tyu5_runs metadata
        'pnl_snapshots',          # Replaced by tyu5_eod_pnl_history
        # NOTE: NOT removing processed_trades as it may still be referenced
    ]
    
    print("=" * 80)
    print("SAFE CLEANUP OF EMPTY LEGACY TABLES")
    print("=" * 80)
    print(f"\nDatabase: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check each table before deletion
    tables_removed = []
    tables_skipped = []
    
    for table in legacy_tables_to_remove:
        try:
            # Check if table exists and is empty
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            if row_count == 0:
                print(f"\n✓ {table}: Empty (0 rows) - Will remove")
                cursor.execute(f"DROP TABLE {table}")
                tables_removed.append(table)
            else:
                print(f"\n✗ {table}: Has data ({row_count} rows) - Skipping")
                tables_skipped.append(table)
                
        except sqlite3.OperationalError as e:
            print(f"\n- {table}: Does not exist or error - {e}")
    
    # Commit changes
    conn.commit()
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if tables_removed:
        print(f"\nTables removed ({len(tables_removed)}):")
        for table in tables_removed:
            print(f"  - {table}")
    else:
        print("\nNo tables were removed.")
    
    if tables_skipped:
        print(f"\nTables skipped ({len(tables_skipped)}):")
        for table in tables_skipped:
            print(f"  - {table}")
    
    # Vacuum to reclaim space
    if tables_removed:
        print("\nVacuuming database to reclaim space...")
        conn.execute("VACUUM")
        print("Done!")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
The following empty tables remain but require manual review:

1. processed_trades - Part of legacy system but may have references
   Consider removing after verifying no active code uses it

2. Empty tables with indexes/foreign keys - These may be:
   - Schema placeholders for future features
   - Part of incomplete implementations
   - Referenced by views or triggers
   
Run 'python scripts/identify_empty_tables.py' to see the full list.
""")

if __name__ == "__main__":
    main() 