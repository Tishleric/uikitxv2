#!/usr/bin/env python
"""
Test TYU5 Schema Migration

This test ensures that the migration successfully creates all required tables
and columns for the TYU5 P&L system integration.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import using direct file path since module name starts with digit
migration_path = Path(__file__).parent.parent.parent / "scripts" / "migration" / "001_add_tyu5_tables.py"
spec = __import__('importlib.util').util.spec_from_file_location("migration_001", migration_path)
migration_module = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(migration_module)
Migration001TYU5Tables = migration_module.Migration001TYU5Tables

from lib.trading.pnl_calculator.storage import PnLStorage


class TestTYU5SchemaMigration:
    """Test suite for TYU5 schema migration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
        
    def test_migration_up(self, temp_db):
        """Test applying the migration creates all required tables."""
        # First initialize base schema with PnLStorage
        storage = PnLStorage(temp_db)
        
        # Apply migration
        migration = Migration001TYU5Tables(temp_db)
        migration.up()
        
        # Verify all tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Check new tables
            expected_tables = [
                'lot_positions',
                'position_greeks',
                'risk_scenarios',
                'match_history',
                'pnl_attribution',
                'schema_migrations'
            ]
            
            for table in expected_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                assert cursor.fetchone() is not None, f"Table {table} not created"
                
            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_lot_positions_symbol',
                'idx_lot_positions_trade',
                'idx_position_greeks_latest',
                'idx_risk_scenarios_latest',
                'idx_match_history_symbol',
                'idx_pnl_attribution_latest'
            ]
            
            for idx in expected_indexes:
                assert idx in indexes, f"Index {idx} not created"
                
            # Check positions table extensions
            cursor.execute("PRAGMA table_info(positions)")
            columns = {row[1] for row in cursor.fetchall()}
            
            assert 'short_quantity' in columns, "short_quantity column not added"
            assert 'match_history' in columns, "match_history column not added"
            
            # Check WAL mode
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == 'WAL', f"Journal mode is {journal_mode}, expected WAL"
            
    def test_migration_status(self, temp_db):
        """Test migration status tracking."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        
        # Check status before migration
        assert not migration.status(), "Migration should not be applied yet"
        
        # Apply migration
        migration.up()
        
        # Check status after migration
        assert migration.status(), "Migration should be marked as applied"
        
        # Verify migration record
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, description FROM schema_migrations 
                WHERE version = '001'
            """)
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == '001'
            assert 'TYU5' in row[1]
            
    def test_lot_positions_table_schema(self, temp_db):
        """Test lot_positions table has correct schema."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        migration.up()
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(lot_positions)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'symbol': 'TEXT',
                'trade_id': 'TEXT',
                'remaining_quantity': 'REAL',
                'entry_price': 'REAL',
                'entry_date': 'DATETIME',
                'position_id': 'INTEGER',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            }
            
            for col, dtype in expected_columns.items():
                assert col in columns, f"Column {col} missing from lot_positions"
                assert columns[col] == dtype, f"Column {col} has type {columns[col]}, expected {dtype}"
                
    def test_position_greeks_table_schema(self, temp_db):
        """Test position_greeks table has correct schema."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        migration.up()
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(position_greeks)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # Check Greek columns exist
            greek_columns = ['delta', 'gamma', 'vega', 'theta', 'speed']
            for greek in greek_columns:
                assert greek in columns, f"Greek column {greek} missing"
                assert columns[greek] == 'REAL', f"Greek column {greek} should be REAL"
                
    def test_risk_scenarios_partial_index(self, temp_db):
        """Test risk_scenarios has partial index for performance."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        migration.up()
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Check index exists with WHERE clause
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='index' AND name='idx_risk_scenarios_latest'
            """)
            
            index_sql = cursor.fetchone()[0]
            assert 'WHERE' in index_sql, "Partial index should have WHERE clause"
            assert '-7 days' in index_sql, "Partial index should use 7-day window"
            
    def test_migration_down(self, temp_db):
        """Test reversing the migration."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        
        # Apply and then reverse
        migration.up()
        migration.down()
        
        # Check tables are dropped
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            dropped_tables = [
                'lot_positions',
                'position_greeks', 
                'risk_scenarios',
                'match_history',
                'pnl_attribution'
            ]
            
            for table in dropped_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                assert cursor.fetchone() is None, f"Table {table} should be dropped"
                
            # Note: positions table columns can't be dropped in SQLite
            # but the migration should handle this gracefully
            
    def test_idempotent_migration(self, temp_db):
        """Test migration can be applied multiple times safely."""
        storage = PnLStorage(temp_db)
        migration = Migration001TYU5Tables(temp_db)
        
        # Apply twice
        migration.up()
        migration.up()  # Should not fail
        
        # Verify only one migration record
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM schema_migrations WHERE version = '001'
            """)
            count = cursor.fetchone()[0]
            assert count == 1, "Should have exactly one migration record"


def test_migration_compatibility():
    """Test that migration is compatible with existing PnLStorage."""
    # Create temporary database
    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Initialize with PnLStorage (creates base schema)
        storage = PnLStorage(temp_db)
        
        # Insert some test data
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO positions (instrument_name, position_quantity, avg_cost, 
                                     total_realized_pnl, unrealized_pnl, last_updated)
                VALUES ('TYU5', 10, 120.5, 0, 0, datetime('now'))
            """)
            conn.commit()
            
        # Apply migration
        migration = Migration001TYU5Tables(temp_db)
        migration.up()
        
        # Verify existing data is preserved
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE instrument_name = 'TYU5'")
            row = cursor.fetchone()
            assert row is not None, "Existing position data lost"
            
            # Check new columns have defaults
            cursor.execute("""
                SELECT short_quantity FROM positions WHERE instrument_name = 'TYU5'
            """)
            short_qty = cursor.fetchone()[0]
            assert short_qty == 0, "Default value for short_quantity not set"
            
    finally:
        os.unlink(temp_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 