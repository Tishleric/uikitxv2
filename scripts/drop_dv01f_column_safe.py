#!/usr/bin/env python3
"""
Safely drop the dv01_f column from FULLPNL table.
This version handles dependent views and uses a different approach.
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
print("FULLPNL Table - dv01_f Column Removal (Safe Version)")
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
for i, col in enumerate(column_names):
    if col == 'dv01_f':
        print(f"  - {col} ← TO BE REMOVED")
    else:
        print(f"  - {col}")

# Step 3: Check if dv01_f exists
if 'dv01_f' not in column_names:
    print("\n✓ Column 'dv01_f' does not exist - nothing to do!")
    conn.close()
    sys.exit(0)

# Step 4: Since we can't easily drop a column in SQLite with dependent views,
# we'll use a different approach - create a completely new table

print("\nApproach: Create FULLPNL_NEW without dv01_f, then swap tables")

# Get columns excluding dv01_f
new_columns = [col for col in column_names if col != 'dv01_f']

# Confirmation
print("\n" + "="*70)
response = input("Proceed with removing dv01_f column? (yes/no): ")
if response.lower() != 'yes':
    print("Operation cancelled.")
    conn.close()
    sys.exit(0)

try:
    # Get the current row count
    cursor.execute("SELECT COUNT(*) FROM FULLPNL")
    original_count = cursor.fetchone()[0]
    print(f"\nOriginal row count: {original_count}")
    
    # Step 1: Create new table
    print("\n1. Creating FULLPNL_NEW without dv01_f...")
    create_sql = """
    CREATE TABLE FULLPNL_NEW (
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
    
    # Step 2: Copy data
    print("2. Copying data (excluding dv01_f)...")
    columns_str = ", ".join(new_columns)
    copy_sql = f"INSERT INTO FULLPNL_NEW ({columns_str}) SELECT {columns_str} FROM FULLPNL"
    conn.execute(copy_sql)
    
    # Verify count
    cursor.execute("SELECT COUNT(*) FROM FULLPNL_NEW")
    new_count = cursor.fetchone()[0]
    print(f"   Copied {new_count} rows")
    
    if new_count != original_count:
        print("❌ Row count mismatch!")
        conn.execute("DROP TABLE FULLPNL_NEW")
        conn.close()
        sys.exit(1)
    
    # Step 3: Drop old table and rename new
    print("3. Swapping tables...")
    conn.execute("DROP TABLE FULLPNL")
    conn.execute("ALTER TABLE FULLPNL_NEW RENAME TO FULLPNL")
    
    conn.commit()
    print("\n✅ Successfully removed dv01_f column!")
    
    # Verify final structure
    cursor.execute("PRAGMA table_info(FULLPNL)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"\nFinal columns ({len(final_columns)}):")
    for col in final_columns:
        print(f"  - {col}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Changes NOT committed")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()

print("\nDone!") 