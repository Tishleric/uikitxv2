#!/usr/bin/env python3
"""
Safely clear P&L tracking data to force reprocessing.
This script:
1. Shows what will be cleared
2. Asks for confirmation
3. Clears only data tables, not schema
"""

import sqlite3
import json
import os
from pathlib import Path

def main():
    # Database path
    db_path = Path("data/output/pnl/pnl_tracker.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all TYU5 tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'tyu5_%' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Found TYU5 tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} rows")
    
    # Check FULLPNL table
    cursor.execute("SELECT COUNT(*) FROM FULLPNL")
    fullpnl_count = cursor.fetchone()[0]
    print(f"\nFULLPNL table: {fullpnl_count} rows")
    
    # Check for processing history JSON
    json_path = Path("data/output/pnl/processing_history.json")
    if json_path.exists():
        with open(json_path, 'r') as f:
            history = json.load(f)
        print(f"\nProcessing history JSON: {len(history)} entries")
    else:
        print("\nNo processing history JSON found")
    
    # Ask for confirmation
    print("\n" + "="*60)
    print("This will DELETE:")
    print("  - All data from TYU5 tables (keeping table structure)")
    print("  - All data from FULLPNL table")
    print("  - Processing history JSON")
    print("="*60)
    
    response = input("\nAre you sure you want to clear this data? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Clear TYU5 tables
    print("\nClearing TYU5 tables...")
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  ✓ Cleared {table}")
        except Exception as e:
            print(f"  ✗ Error clearing {table}: {e}")
    
    # Clear FULLPNL
    print("\nClearing FULLPNL table...")
    try:
        cursor.execute("DELETE FROM FULLPNL")
        print("  ✓ Cleared FULLPNL")
    except Exception as e:
        print(f"  ✗ Error clearing FULLPNL: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Clear processing history JSON
    if json_path.exists():
        print("\nClearing processing history JSON...")
        try:
            # Create empty JSON
            with open(json_path, 'w') as f:
                json.dump({}, f)
            print("  ✓ Cleared processing history")
        except Exception as e:
            print(f"  ✗ Error clearing JSON: {e}")
    
    print("\nData cleared successfully!")
    print("The file watchers will reprocess all trades on next run.")


if __name__ == "__main__":
    main() 