#!/usr/bin/env python3
"""
Test Spot Risk Price Updates

Purpose: Test the spot risk price watcher with sample data
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_fifo_lifo import (
    create_all_tables, 
    update_current_price,
    load_pricing_dictionaries
)


def test_price_updates():
    """Test updating prices in the database."""
    
    # Create test database
    db_path = 'test_trades.db'
    conn = sqlite3.connect(db_path)
    
    print("Creating tables...")
    create_all_tables(conn)
    
    # Test price updates
    test_prices = [
        ('TYU5 Comdty', 110.828125, datetime(2025, 7, 25, 14, 30, 0)),
        ('TYU5C 111.750 Comdty', 0.453125, datetime(2025, 7, 25, 14, 30, 0)),
        ('TYU5P 110.500 Comdty', 0.234375, datetime(2025, 7, 25, 14, 30, 0)),
    ]
    
    print("\nUpdating prices...")
    for symbol, price, timestamp in test_prices:
        success = update_current_price(conn, symbol, price, timestamp)
        print(f"  {symbol}: {price} - {'Success' if success else 'Failed'}")
    
    # Load and display prices
    print("\nLoading prices from database...")
    price_dicts = load_pricing_dictionaries(conn)
    
    print("\nCurrent prices (now):")
    for symbol, price in price_dicts.get('now', {}).items():
        print(f"  {symbol}: {price}")
    
    # Query pricing table directly
    print("\nDirect query of pricing table:")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pricing ORDER BY symbol")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()
    
    # Clean up test database
    Path(db_path).unlink(missing_ok=True)
    print("\nTest completed successfully!")


if __name__ == '__main__':
    test_price_updates() 