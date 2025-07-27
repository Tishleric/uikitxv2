#!/usr/bin/env python3
"""
Test script to verify watchers setup
"""

import sqlite3
import os
from pathlib import Path

# Add lib to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.pnl_fifo_lifo import (
    create_all_tables,
    TradeLedgerWatcher,
    SpotRiskPriceWatcher
)

def test_database_setup():
    """Test that database can be created in root folder"""
    print("Testing database setup...")
    
    # Database path in root folder
    db_path = 'trades.db'
    
    # Create database if it doesn't exist
    if not os.path.exists(db_path):
        print(f"Creating new database: {db_path}")
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        conn.close()
    else:
        print(f"Database already exists: {db_path}")
    
    # Verify tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for processed_files table
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='processed_files'
    """)
    
    if cursor.fetchone():
        print("✓ processed_files table exists")
    else:
        print("✗ processed_files table missing - creating tables...")
        create_all_tables(conn)
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")
    
    conn.close()

def test_watchers():
    """Test that watchers can be instantiated"""
    print("\nTesting watchers...")
    
    db_path = 'trades.db'
    
    # Test Trade Ledger Watcher
    try:
        trade_watcher = TradeLedgerWatcher(db_path, 'data/input/trade_ledger')
        print("✓ TradeLedgerWatcher created successfully")
    except Exception as e:
        print(f"✗ TradeLedgerWatcher error: {e}")
    
    # Test Spot Risk Price Watcher
    try:
        price_watcher = SpotRiskPriceWatcher(db_path, 'data/input/actant_spot_risk')
        print("✓ SpotRiskPriceWatcher created successfully")
    except Exception as e:
        print(f"✗ SpotRiskPriceWatcher error: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("Watcher Setup Test")
    print("=" * 60)
    
    test_database_setup()
    test_watchers()
    
    print("\nTest complete!") 