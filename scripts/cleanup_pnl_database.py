#!/usr/bin/env python3
"""
Clean up pnl_tracker.db by dropping all tables except fullpnl.
"""

import sqlite3
import os
from datetime import datetime

def cleanup_pnl_database():
    """Drop all tables except fullpnl from pnl_tracker.db."""
    db_path = 'data/output/pnl/pnl_tracker.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Cleaning up database: {db_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get list of all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(all_tables)} tables:")
        for table in sorted(all_tables):
            print(f"  - {table}")
        
        # Drop all tables except fullpnl
        print("\nDropping tables...")
        dropped_count = 0
        kept_count = 0
        
        for table in all_tables:
            if table.lower() == 'fullpnl':
                print(f"  ✓ KEEPING: {table}")
                kept_count += 1
            else:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  ✗ DROPPED: {table}")
                dropped_count += 1
        
        conn.commit()
        
        # Verify remaining tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        remaining_tables = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "-" * 80)
        print(f"Cleanup complete:")
        print(f"  - Tables dropped: {dropped_count}")
        print(f"  - Tables kept: {kept_count}")
        print(f"  - Remaining tables: {remaining_tables}")
        
        # Vacuum to reclaim space
        print("\nVacuuming database to reclaim space...")
        conn.execute("VACUUM")
        
        return True
        
    except Exception as e:
        print(f"\nERROR during cleanup: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = cleanup_pnl_database()
    exit(0 if success else 1) 