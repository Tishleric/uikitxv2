#!/usr/bin/env python3
"""
Migration 002: Add EOD P&L History Table

This migration creates the tyu5_eod_pnl_history table for storing
daily P&L snapshots at 4pm with settlement-aware calculations.
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
    """Apply migration - create EOD history table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create the EOD history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tyu5_eod_pnl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL,
                symbol TEXT NOT NULL,
                position_quantity REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl_settle REAL NOT NULL,  -- Using px_settle
                unrealized_pnl_current REAL NOT NULL,  -- Using current 4pm price
                total_daily_pnl REAL NOT NULL,
                settlement_price REAL,  -- px_settle used
                current_price REAL,     -- 4pm price used
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(snapshot_date, symbol)
            )
        """)
        
        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eod_history_date 
            ON tyu5_eod_pnl_history(snapshot_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eod_history_symbol 
            ON tyu5_eod_pnl_history(symbol)
        """)
        
        # Create view for latest snapshot per symbol
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_latest_eod_snapshot AS
            SELECT * FROM tyu5_eod_pnl_history
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM tyu5_eod_pnl_history)
        """)
        
        # Create aggregated view for daily totals
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_daily_pnl_totals AS
            SELECT 
                snapshot_date,
                COUNT(DISTINCT symbol) as symbol_count,
                SUM(CASE WHEN symbol NOT LIKE '%Comdty%' THEN 0 ELSE position_quantity END) as futures_position,
                SUM(CASE WHEN symbol LIKE '%Comdty%' THEN 0 ELSE position_quantity END) as options_position,
                SUM(realized_pnl) as total_realized,
                SUM(unrealized_pnl_settle) as total_unrealized_settle,
                SUM(unrealized_pnl_current) as total_unrealized_current,
                SUM(total_daily_pnl) as total_pnl
            FROM tyu5_eod_pnl_history
            WHERE symbol != 'TOTAL'
            GROUP BY snapshot_date
        """)
        
        conn.commit()
        logger.info("Successfully created tyu5_eod_pnl_history table and views")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


def migrate_down(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Rollback migration - drop EOD history table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP VIEW IF EXISTS tyu5_daily_pnl_totals")
        cursor.execute("DROP VIEW IF EXISTS tyu5_latest_eod_snapshot")
        cursor.execute("DROP TABLE IF EXISTS tyu5_eod_pnl_history")
        conn.commit()
        logger.info("Successfully rolled back EOD history table")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Rollback failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EOD History Table Migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--db-path", help="Database path", default="data/output/pnl/pnl_tracker.db")
    
    args = parser.parse_args()
    
    if args.rollback:
        migrate_down(args.db_path)
    else:
        migrate_up(args.db_path) 