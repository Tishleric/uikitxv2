#!/usr/bin/env python
"""
Migration: Add TYU5 P&L System Tables
Version: 001
Date: January 2025

This migration adds the following tables to support TYU5's advanced P&L features:
- lot_positions: Individual lot tracking with FIFO matching
- position_greeks: Greek values (delta, gamma, vega, theta, speed) per position
- risk_scenarios: Price scenario analysis data

Also extends existing tables:
- positions: Adds short_quantity and match_history columns
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class Migration001TYU5Tables:
    """Add TYU5 P&L system tables and extensions."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        """Initialize migration with database path."""
        self.db_path = db_path
        self.version = "001"
        self.description = "Add TYU5 P&L system tables"
        
    def up(self):
        """Apply the migration - add new tables and columns."""
        logger.info(f"Applying migration {self.version}: {self.description}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency (as mentioned in the plan)
            cursor.execute("PRAGMA journal_mode=WAL;")
            
            # 1. Create lot_positions table for individual lot tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lot_positions (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    remaining_quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    entry_date DATETIME NOT NULL,
                    position_id INTEGER REFERENCES positions(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Index for efficient lot lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lot_positions_symbol 
                ON lot_positions(symbol);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lot_positions_trade 
                ON lot_positions(trade_id, entry_date);
            """)
            
            # 2. Create position_greeks table for Greek values
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS position_greeks (
                    id INTEGER PRIMARY KEY,
                    position_id INTEGER REFERENCES positions(id),
                    calc_timestamp DATETIME NOT NULL,
                    underlying_price REAL NOT NULL,
                    implied_vol REAL,
                    delta REAL,
                    gamma REAL,
                    vega REAL,
                    theta REAL,
                    speed REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Index for latest Greek lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_position_greeks_latest 
                ON position_greeks(position_id, calc_timestamp DESC);
            """)
            
            # 3. Create risk_scenarios table for scenario analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_scenarios (
                    id INTEGER PRIMARY KEY,
                    calc_timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    scenario_price REAL NOT NULL,
                    scenario_pnl REAL NOT NULL,
                    scenario_delta REAL,
                    scenario_gamma REAL,
                    position_quantity REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Partial index for latest scenarios (as mentioned in the plan)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_risk_scenarios_latest 
                ON risk_scenarios(symbol, calc_timestamp DESC)
                WHERE calc_timestamp > datetime('now', '-7 days');
            """)
            
            # 4. Extend positions table with new columns
            # Check if columns already exist before adding
            cursor.execute("PRAGMA table_info(positions)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'short_quantity' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE positions 
                    ADD COLUMN short_quantity REAL NOT NULL DEFAULT 0;
                """)
                
            if 'match_history' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE positions 
                    ADD COLUMN match_history TEXT;  -- JSON column for match details
                """)
                
            # 5. Create match_history table for detailed FIFO matching
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_history (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    match_date DATETIME NOT NULL,
                    buy_trade_id TEXT NOT NULL,
                    sell_trade_id TEXT NOT NULL,
                    matched_quantity REAL NOT NULL,
                    buy_price REAL NOT NULL,
                    sell_price REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Index for match history lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_match_history_symbol 
                ON match_history(symbol, match_date DESC);
            """)
            
            # 6. Create P&L attribution table for Bachelier decomposition
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pnl_attribution (
                    id INTEGER PRIMARY KEY,
                    position_id INTEGER REFERENCES positions(id),
                    calc_timestamp DATETIME NOT NULL,
                    total_pnl REAL NOT NULL,
                    delta_pnl REAL,
                    gamma_pnl REAL,
                    vega_pnl REAL,
                    theta_pnl REAL,
                    speed_pnl REAL,
                    residual_pnl REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Index for attribution lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pnl_attribution_latest 
                ON pnl_attribution(position_id, calc_timestamp DESC);
            """)
            
            # 7. Create migration tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Record this migration
            cursor.execute("""
                INSERT OR IGNORE INTO schema_migrations (version, description)
                VALUES (?, ?);
            """, (self.version, self.description))
            
            conn.commit()
            logger.info(f"Migration {self.version} applied successfully")
            
    def down(self):
        """Reverse the migration - drop new tables and columns."""
        logger.info(f"Reversing migration {self.version}: {self.description}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Drop new tables (in reverse order of creation)
            tables_to_drop = [
                'pnl_attribution',
                'match_history',
                'risk_scenarios',
                'position_greeks',
                'lot_positions'
            ]
            
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
                
            # Note: SQLite doesn't support dropping columns easily
            # In production, we'd need to recreate the positions table
            # For now, we'll just log a warning
            logger.warning(
                "Cannot drop columns from positions table in SQLite. "
                "Manual intervention required to remove short_quantity and match_history columns."
            )
            
            # Remove migration record
            cursor.execute("""
                DELETE FROM schema_migrations WHERE version = ?;
            """, (self.version,))
            
            conn.commit()
            logger.info(f"Migration {self.version} reversed successfully")
            
    def status(self) -> bool:
        """Check if this migration has been applied."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if migration tracking table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_migrations';
            """)
            
            if not cursor.fetchone():
                return False
                
            # Check if this migration has been applied
            cursor.execute("""
                SELECT 1 FROM schema_migrations WHERE version = ?;
            """, (self.version,))
            
            return cursor.fetchone() is not None


def main():
    """Run the migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TYU5 Tables Migration")
    parser.add_argument('action', choices=['up', 'down', 'status'],
                       help="Migration action to perform")
    parser.add_argument('--db-path', default="data/output/pnl/pnl_tracker.db",
                       help="Path to database file")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    migration = Migration001TYU5Tables(args.db_path)
    
    if args.action == 'up':
        migration.up()
    elif args.action == 'down':
        migration.down()
    elif args.action == 'status':
        applied = migration.status()
        print(f"Migration {migration.version} is {'applied' if applied else 'not applied'}")


if __name__ == "__main__":
    main() 