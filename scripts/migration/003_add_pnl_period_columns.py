#!/usr/bin/env python3
"""
Migration 003: Add P&L Period Tracking Columns

This migration adds columns to track the actual P&L period boundaries
and make it clear that P&L days run from 2pm to 2pm.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_up(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Apply migration - add P&L period tracking columns."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add period tracking columns
        cursor.execute("""
            ALTER TABLE tyu5_eod_pnl_history
            ADD COLUMN pnl_period_start TIMESTAMP
        """)
        
        cursor.execute("""
            ALTER TABLE tyu5_eod_pnl_history
            ADD COLUMN pnl_period_end TIMESTAMP
        """)
        
        cursor.execute("""
            ALTER TABLE tyu5_eod_pnl_history
            ADD COLUMN trades_in_period INTEGER DEFAULT 0
        """)
        
        # Create a view that clearly shows P&L periods
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_pnl_periods AS
            SELECT 
                snapshot_date as pnl_date,
                datetime(snapshot_date, '-1 day', '+14 hours') as period_start_approx,
                datetime(snapshot_date, '+14 hours') as period_end_approx,
                pnl_period_start,
                pnl_period_end,
                COUNT(CASE WHEN symbol != 'TOTAL' THEN 1 END) as position_count,
                MAX(CASE WHEN symbol = 'TOTAL' THEN total_daily_pnl END) as total_period_pnl,
                MAX(CASE WHEN symbol = 'TOTAL' THEN trades_in_period END) as trades_count
            FROM tyu5_eod_pnl_history
            GROUP BY snapshot_date
            ORDER BY snapshot_date DESC
        """)
        
        # Create index for period queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eod_period_start 
            ON tyu5_eod_pnl_history(pnl_period_start)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Successfully added P&L period tracking columns")
        logger.info("Note: snapshot_date represents the P&L date (period ends at 2pm on this date)")
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Migration failed: {e}")
        raise


def migrate_down(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Rollback migration - remove P&L period tracking."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support dropping columns easily
        # We would need to recreate the table without these columns
        # For now, just drop the view
        
        cursor.execute("DROP VIEW IF EXISTS tyu5_pnl_periods")
        cursor.execute("DROP INDEX IF EXISTS idx_eod_period_start")
        
        conn.commit()
        conn.close()
        
        logger.info("Rolled back migration (columns remain but view removed)")
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down()
    else:
        migrate_up() 