#!/usr/bin/env python3
"""
Migration 004: Add P&L Components Table

This migration adds tables to store settlement-aware P&L component breakdowns
and updates the position breakdown table with timestamp columns.
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
    """Apply migration - add P&L components tracking."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create P&L components table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tyu5_pnl_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                component_type TEXT NOT NULL,  -- 'intraday', 'entry_to_settle', 'settle_to_settle', 'settle_to_exit'
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                start_price REAL NOT NULL,
                end_price REAL NOT NULL,
                quantity REAL NOT NULL,
                pnl_amount REAL NOT NULL,
                calculation_run_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pnl_components_lot 
            ON tyu5_pnl_components(lot_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pnl_components_symbol_time 
            ON tyu5_pnl_components(symbol, end_time)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pnl_components_run 
            ON tyu5_pnl_components(calculation_run_id)
        """)
        
        # Check if position breakdown table exists and add timestamp columns
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tyu5_position_breakdown'
        """)
        
        if cursor.fetchone():
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(tyu5_position_breakdown)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'entry_datetime' not in columns:
                cursor.execute("""
                    ALTER TABLE tyu5_position_breakdown 
                    ADD COLUMN entry_datetime TIMESTAMP
                """)
                logger.info("Added entry_datetime column to tyu5_position_breakdown")
            
            if 'exit_datetime' not in columns:
                cursor.execute("""
                    ALTER TABLE tyu5_position_breakdown 
                    ADD COLUMN exit_datetime TIMESTAMP
                """)
                logger.info("Added exit_datetime column to tyu5_position_breakdown")
            
            if 'settlement_splits' not in columns:
                cursor.execute("""
                    ALTER TABLE tyu5_position_breakdown 
                    ADD COLUMN settlement_splits TEXT
                """)
                logger.info("Added settlement_splits column to tyu5_position_breakdown")
        
        # Create view for P&L component summary
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_pnl_component_summary AS
            SELECT 
                symbol,
                component_type,
                COUNT(*) as component_count,
                SUM(pnl_amount) as total_pnl,
                MIN(start_time) as earliest_start,
                MAX(end_time) as latest_end,
                calculation_run_id
            FROM tyu5_pnl_components
            GROUP BY symbol, component_type, calculation_run_id
            ORDER BY symbol, component_type
        """)
        
        # Create view for daily P&L by component
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tyu5_daily_pnl_components AS
            SELECT 
                DATE(end_time) as pnl_date,
                symbol,
                component_type,
                SUM(pnl_amount) as component_pnl,
                COUNT(*) as lot_count
            FROM tyu5_pnl_components
            GROUP BY DATE(end_time), symbol, component_type
            ORDER BY pnl_date DESC, symbol
        """)
        
        # Create alerts table for missing prices and other issues
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tyu5_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,  -- JSON data
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_type_resolved 
            ON tyu5_alerts(alert_type, resolved)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Successfully created P&L components table and views")
        logger.info("Settlement-aware P&L tracking infrastructure ready")
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Migration failed: {e}")
        raise


def migrate_down(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Rollback migration - remove P&L components tracking."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop views
        cursor.execute("DROP VIEW IF EXISTS tyu5_daily_pnl_components")
        cursor.execute("DROP VIEW IF EXISTS tyu5_pnl_component_summary")
        
        # Drop table
        cursor.execute("DROP TABLE IF EXISTS tyu5_pnl_components")
        
        # Note: Cannot easily remove columns from tyu5_position_breakdown in SQLite
        # Would need to recreate the table without those columns
        
        conn.commit()
        conn.close()
        
        logger.info("Rolled back P&L components migration")
        
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