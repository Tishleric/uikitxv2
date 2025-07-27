#!/usr/bin/env python3
"""
Inspect the test database to verify watcher functionality
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def inspect_test_db(db_path='trades_test.db'):
    """Inspect the test database contents"""
    
    if not Path(db_path).exists():
        print(f"Test database '{db_path}' does not exist!")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n{'='*60}")
    print(f"Inspecting Test Database: {db_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Get all tables
    tables = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """).fetchall()
    
    print(f"Tables found: {len(tables)}")
    for table in tables:
        table_name = table[0]
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  - {table_name}: {count} rows")
    
    # Show recent trades
    print(f"\n{'='*60}")
    print("Recent Trades (FIFO):")
    print(f"{'='*60}")
    
    recent_trades = cursor.execute("""
        SELECT transactionId, symbol, buySell, quantity, price, time
        FROM trades_fifo
        ORDER BY time DESC
        LIMIT 5
    """).fetchall()
    
    if recent_trades:
        print(f"{'TransID':<10} {'Symbol':<20} {'B/S':<5} {'Qty':<8} {'Price':<10} {'Time'}")
        print("-" * 75)
        for trade in recent_trades:
            print(f"{trade[0]:<10} {trade[1]:<20} {trade[2]:<5} {trade[3]:<8.2f} {trade[4]:<10.4f} {trade[5]}")
    else:
        print("No trades found")
    
    # Show recent prices
    print(f"\n{'='*60}")
    print("Recent Prices:")
    print(f"{'='*60}")
    
    recent_prices = cursor.execute("""
        SELECT symbol, price_type, price, timestamp
        FROM pricing
        ORDER BY timestamp DESC
        LIMIT 5
    """).fetchall()
    
    if recent_prices:
        print(f"{'Symbol':<20} {'Type':<10} {'Price':<12} {'Timestamp'}")
        print("-" * 60)
        for price in recent_prices:
            print(f"{price[0]:<20} {price[1]:<10} {price[2]:<12.4f} {price[3]}")
    else:
        print("No prices found")
    
    # Show processed files
    print(f"\n{'='*60}")
    print("Processed Files Status:")
    print(f"{'='*60}")
    
    processed_files = cursor.execute("""
        SELECT file_path, processed_at, trade_count
        FROM processed_files
        ORDER BY processed_at DESC
        LIMIT 10
    """).fetchall()
    
    if processed_files:
        for pf in processed_files:
            filename = Path(pf[0]).name
            print(f"{filename:<40} Processed: {pf[1]:<20} Lines: {pf[2]}")
    else:
        print("No processed files recorded")
    
    conn.close()
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'trades_test.db'
    inspect_test_db(db_path) 