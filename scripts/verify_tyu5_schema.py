#!/usr/bin/env python
"""Verify TYU5 Schema Migration

This script checks that all required tables and columns for the TYU5 P&L system
have been successfully created in the database.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage


def verify_schema(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Verify that TYU5 schema has been properly applied."""
    print(f"\nVerifying TYU5 schema in database: {db_path}")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check WAL mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"\n✓ Journal Mode: {journal_mode} (should be WAL)")
        
        # Check new tables
        print("\n=== New Tables ===")
        new_tables = [
            'lot_positions',
            'position_greeks', 
            'risk_scenarios',
            'match_history',
            'pnl_attribution',
            'schema_migrations'
        ]
        
        for table in new_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            exists = cursor.fetchone() is not None
            print(f"{'✓' if exists else '✗'} {table}: {'EXISTS' if exists else 'MISSING'}")
            
        # Check indexes
        print("\n=== Indexes ===")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%' 
            ORDER BY name
        """)
        indexes = cursor.fetchall()
        
        expected_indexes = [
            'idx_lot_positions_symbol',
            'idx_lot_positions_trade',
            'idx_position_greeks_latest',
            'idx_risk_scenarios_latest',
            'idx_match_history_symbol',
            'idx_pnl_attribution_latest'
        ]
        
        existing_indexes = [row[0] for row in indexes]
        
        for idx in expected_indexes:
            exists = idx in existing_indexes
            print(f"{'✓' if exists else '✗'} {idx}: {'EXISTS' if exists else 'MISSING'}")
            
        # Check positions table extensions
        print("\n=== Positions Table Extensions ===")
        cursor.execute("PRAGMA table_info(positions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        new_columns = ['short_quantity', 'match_history']
        for col in new_columns:
            exists = col in columns
            print(f"{'✓' if exists else '✗'} {col}: {'EXISTS' if exists else 'MISSING'}")
            
        # Check schema migration record
        print("\n=== Migration Record ===")
        cursor.execute("""
            SELECT version, description, applied_at 
            FROM schema_migrations 
            WHERE version = '001'
        """)
        migration = cursor.fetchone()
        
        if migration:
            print(f"✓ Migration {migration[0]}: {migration[1]}")
            print(f"  Applied at: {migration[2]}")
        else:
            print("✗ Migration 001 not recorded")
            
        # Sample table structures
        print("\n=== Sample Table Structures ===")
        
        # Lot positions
        print("\nlot_positions table:")
        cursor.execute("PRAGMA table_info(lot_positions)")
        for row in cursor.fetchall():
            print(f"  {row[1]} {row[2]}")
            
        # Position Greeks
        print("\nposition_greeks table:")
        cursor.execute("PRAGMA table_info(position_greeks)")
        for row in cursor.fetchall():
            print(f"  {row[1]} {row[2]}")
            
        # Check partial index SQL
        print("\n=== Partial Index Check ===")
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='index' AND name='idx_risk_scenarios_latest'
        """)
        index_sql = cursor.fetchone()
        if index_sql:
            print(f"✓ Risk scenarios partial index SQL:")
            print(f"  {index_sql[0]}")
        else:
            print("✗ Risk scenarios partial index not found")
            
    print("\n" + "=" * 60)
    print("Schema verification complete!\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify TYU5 schema migration")
    parser.add_argument('--db-path', default="data/output/pnl/pnl_tracker.db",
                       help="Path to database file")
    
    args = parser.parse_args()
    verify_schema(args.db_path) 