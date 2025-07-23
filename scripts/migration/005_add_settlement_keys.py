#!/usr/bin/env python3
"""
Add settlement keys to P&L components and create open lot snapshots table.

This migration:
1. Adds settlement key columns to tyu5_pnl_components
2. Creates tyu5_open_lot_snapshots table for 2pm position tracking
3. Creates indexes for efficient period queries
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def main():
    """Run the migration."""
    db_path = project_root / "data" / "output" / "pnl" / "pnl_tracker.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add settlement key columns to tyu5_pnl_components
        print("Adding settlement key columns...")
        cursor.execute("""
            ALTER TABLE tyu5_pnl_components 
            ADD COLUMN start_settlement_key TEXT
        """)
        
        cursor.execute("""
            ALTER TABLE tyu5_pnl_components 
            ADD COLUMN end_settlement_key TEXT
        """)
        
        # Create open lot snapshots table
        print("Creating open lot snapshots table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tyu5_open_lot_snapshots (
                lot_id TEXT NOT NULL,
                settlement_key TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity_remaining REAL NOT NULL,
                entry_price REAL NOT NULL,
                entry_datetime TIMESTAMP NOT NULL,
                mark_price REAL,  -- Current price at 2pm
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lot_id, settlement_key)
            )
        """)
        
        # Create indexes for efficient queries
        print("Creating indexes...")
        
        # Index for P&L component period queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pnl_components_settlement_keys 
            ON tyu5_pnl_components(start_settlement_key, end_settlement_key)
        """)
        
        # Index for snapshot queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_open_lot_snapshots_settlement_key 
            ON tyu5_open_lot_snapshots(settlement_key)
        """)
        
        # Create a view for easy EOD P&L queries
        print("Creating EOD P&L view...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_eod_pnl_by_period AS
            SELECT 
                start_settlement_key,
                end_settlement_key,
                symbol,
                SUM(pnl_amount) as period_pnl,
                COUNT(*) as component_count,
                GROUP_CONCAT(DISTINCT component_type) as component_types
            FROM tyu5_pnl_components
            WHERE start_settlement_key IS NOT NULL 
              AND end_settlement_key IS NOT NULL
            GROUP BY start_settlement_key, end_settlement_key, symbol
        """)
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Show current schema
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='tyu5_pnl_components'
        """)
        result = cursor.fetchone()
        if result:
            print("\nUpdated tyu5_pnl_components schema:")
            print(result[0])
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main() 