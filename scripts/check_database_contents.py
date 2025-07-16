"""Check database contents to identify stale data issues."""

import sqlite3
from datetime import datetime

def check_database(db_path):
    """Check database contents and date ranges."""
    print(f"\n=== Checking database: {db_path} ===\n")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check tables in database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  - {table['name']}")
    
    # 2. Check processed_trades table
    print("\n--- PROCESSED TRADES ---")
    cursor.execute("SELECT COUNT(*) as count FROM processed_trades")
    count = cursor.fetchone()['count']
    print(f"Total processed trades: {count}")
    
    if count > 0:
        # Get date range
        cursor.execute("""
            SELECT 
                MIN(trade_date) as earliest_date,
                MAX(trade_date) as latest_date,
                COUNT(DISTINCT trade_date) as unique_dates
            FROM processed_trades
        """)
        row = cursor.fetchone()
        print(f"Date range: {row['earliest_date']} to {row['latest_date']}")
        print(f"Unique dates: {row['unique_dates']}")
        
        # Show sample trades with dates
        cursor.execute("""
            SELECT trade_date, instrument_name, quantity, price, source_file
            FROM processed_trades
            ORDER BY trade_date DESC
            LIMIT 5
        """)
        print("\nLatest 5 trades:")
        for row in cursor.fetchall():
            print(f"  {row['trade_date']} | {row['instrument_name']} | qty={row['quantity']} | price={row['price']} | from: {row['source_file']}")
    
    # 3. Check positions table
    print("\n--- POSITIONS ---")
    cursor.execute("SELECT COUNT(*) as count FROM positions")
    count = cursor.fetchone()['count']
    print(f"Total positions: {count}")
    
    if count > 0:
        # Check last updated times
        cursor.execute("""
            SELECT 
                instrument_name,
                position_quantity,
                last_updated,
                last_trade_id
            FROM positions
            ORDER BY last_updated DESC
            LIMIT 5
        """)
        print("\nPositions by last update:")
        for row in cursor.fetchall():
            print(f"  {row['last_updated']} | {row['instrument_name']} | qty={row['position_quantity']} | trade_id={row['last_trade_id']}")
    
    # 4. Check market_prices table
    print("\n--- MARKET PRICES ---")
    cursor.execute("SELECT COUNT(*) as count FROM market_prices")
    count = cursor.fetchone()['count']
    print(f"Total market prices: {count}")
    
    if count > 0:
        # First check the schema
        cursor.execute("PRAGMA table_info(market_prices)")
        columns = cursor.fetchall()
        print("Market prices columns:", [col[1] for col in columns])
        
        # Check for timestamp columns
        timestamp_col = None
        for col in columns:
            if 'time' in col[1].lower() or 'date' in col[1].lower():
                timestamp_col = col[1]
                break
        
        if timestamp_col:
            cursor.execute(f"""
                SELECT 
                    MIN({timestamp_col}) as earliest,
                    MAX({timestamp_col}) as latest,
                    COUNT(DISTINCT DATE({timestamp_col})) as unique_dates
                FROM market_prices
            """)
            row = cursor.fetchone()
            print(f"Price date range: {row['earliest']} to {row['latest']}")
            print(f"Unique price dates: {row['unique_dates']}")
    
    conn.close()

# Check the pnl_tracker.db
check_database("data/output/pnl/pnl_tracker.db")

# Also check if there are other PnL databases
print("\n=== Checking for other PnL databases ===")
import os
pnl_dir = "data/output/pnl"
for file in os.listdir(pnl_dir):
    if file.endswith('.db'):
        print(f"\nFound database: {file}")
        if file != "pnl_tracker.db":
            check_database(os.path.join(pnl_dir, file)) 