#!/usr/bin/env python3
"""
Safely drop the dv01_f column from FULLPNL table.
This script includes multiple safety checks to prevent accidents.
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path("data/output/pnl/pnl_tracker.db")

if not DB_PATH.exists():
    print(f"❌ Database not found: {DB_PATH}")
    sys.exit(1)

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("FULLPNL Table - dv01_f Column Removal")
print("=" * 70)

# Step 1: Check if FULLPNL table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FULLPNL'")
if not cursor.fetchone():
    print("❌ FULLPNL table does not exist!")
    conn.close()
    sys.exit(1)

print("✓ FULLPNL table exists")

# Step 2: Get current columns
cursor.execute("PRAGMA table_info(FULLPNL)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"\nCurrent columns ({len(column_names)}):")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Step 3: Check if dv01_f exists
if 'dv01_f' not in column_names:
    print("\n✓ Column 'dv01_f' does not exist - nothing to do!")
    conn.close()
    sys.exit(0)

# Step 4: Check if dv01_f has any non-null data
cursor.execute("SELECT COUNT(*) FROM FULLPNL WHERE dv01_f IS NOT NULL")
non_null_count = cursor.fetchone()[0]

print(f"\n⚠️  Column 'dv01_f' exists")
print(f"   - Non-null values: {non_null_count}")

# Step 5: Create backup of current data
print("\nCreating backup...")
cursor.execute("SELECT COUNT(*) FROM FULLPNL")
total_rows = cursor.fetchone()[0]
print(f"   - Total rows: {total_rows}")

# Step 6: Since SQLite doesn't support DROP COLUMN directly,
# we need to recreate the table without the column

print("\nPlan: Recreate FULLPNL table without dv01_f column")
print("This will preserve all other data.")

# Get the list of columns excluding dv01_f
new_columns = [col for col in column_names if col != 'dv01_f']
print(f"\nNew column list ({len(new_columns)}):")
for col in new_columns:
    print(f"  - {col}")

# Confirmation
print("\n" + "="*70)
response = input("Proceed with dropping dv01_f column? (yes/no): ")
if response.lower() != 'yes':
    print("Operation cancelled.")
    conn.close()
    sys.exit(0)

try:
    # Begin transaction
    conn.execute("BEGIN TRANSACTION")
    
    # Step 1: Rename existing table
    print("\n1. Renaming existing table to FULLPNL_backup...")
    conn.execute("ALTER TABLE FULLPNL RENAME TO FULLPNL_backup")
    
    # Step 2: Create new table without dv01_f
    print("2. Creating new FULLPNL table without dv01_f...")
    create_sql = """
    CREATE TABLE FULLPNL (
        -- Identity columns
        symbol_tyu5 TEXT PRIMARY KEY,
        symbol_bloomberg TEXT,
        type TEXT,
        
        -- Position data from tyu5_positions
        net_quantity REAL,
        closed_quantity REAL,
        avg_entry_price REAL,
        current_price REAL,
        flash_close REAL,
        prior_close REAL,
        current_present_value REAL,
        prior_present_value REAL,
        unrealized_pnl_current REAL,
        unrealized_pnl_flash REAL,
        unrealized_pnl_close REAL,
        realized_pnl REAL,
        daily_pnl REAL,
        total_pnl REAL,
        
        -- Greeks F-space from spot_risk (NO dv01_f)
        vtexp REAL,
        delta_f REAL,
        gamma_f REAL,
        speed_f REAL,
        theta_f REAL,
        vega_f REAL,
        
        -- Greeks Y-space from spot_risk
        dv01_y REAL,
        delta_y REAL,
        gamma_y REAL,
        speed_y REAL,
        theta_y REAL,
        vega_y REAL,
        
        -- Metadata
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        spot_risk_file TEXT,
        tyu5_run_id TEXT
    );
    """
    conn.execute(create_sql)
    
    # Step 3: Copy data from backup (excluding dv01_f)
    print("3. Copying data from backup (excluding dv01_f)...")
    columns_str = ", ".join(new_columns)
    copy_sql = f"INSERT INTO FULLPNL ({columns_str}) SELECT {columns_str} FROM FULLPNL_backup"
    conn.execute(copy_sql)
    
    # Step 4: Verify row count
    cursor.execute("SELECT COUNT(*) FROM FULLPNL")
    new_count = cursor.fetchone()[0]
    print(f"   - Copied {new_count} rows (expected: {total_rows})")
    
    if new_count != total_rows:
        print("❌ Row count mismatch! Rolling back...")
        conn.rollback()
        sys.exit(1)
    
    # Step 5: Drop backup table
    print("4. Dropping backup table...")
    conn.execute("DROP TABLE FULLPNL_backup")
    
    # Commit transaction
    conn.commit()
    print("\n✅ Successfully removed dv01_f column from FULLPNL table!")
    
    # Verify final structure
    cursor.execute("PRAGMA table_info(FULLPNL)")
    final_columns = cursor.fetchall()
    print(f"\nFinal column count: {len(final_columns)}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Rolling back changes...")
    conn.rollback()
    # Try to restore backup if it exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FULLPNL_backup'")
    if cursor.fetchone():
        print("Restoring from backup...")
        conn.execute("DROP TABLE IF EXISTS FULLPNL")
        conn.execute("ALTER TABLE FULLPNL_backup RENAME TO FULLPNL")
        conn.commit()
    sys.exit(1)
finally:
    conn.close()

print("\nDone!") 