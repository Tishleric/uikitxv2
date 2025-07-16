import sqlite3
from pathlib import Path

# Check market prices database
db_path = Path("data/output/market_prices/market_prices.db")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in market_prices.db: {tables}")
    
    # Check futures_prices table
    if 'futures_prices' in tables:
        cursor.execute("SELECT COUNT(*) FROM futures_prices")
        count = cursor.fetchone()[0]
        print(f"\nTotal futures prices: {count}")
        
        # Show columns
        cursor.execute("PRAGMA table_info(futures_prices)")
        columns = cursor.fetchall()
        print("\nFutures table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show sample records
        cursor.execute("SELECT * FROM futures_prices LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("\nSample futures records:")
            for row in rows:
                print(row)
    
    # Check options_prices table
    if 'options_prices' in tables:
        cursor.execute("SELECT COUNT(*) FROM options_prices")
        count = cursor.fetchone()[0]
        print(f"\nTotal options prices: {count}")
        
        # Show columns
        cursor.execute("PRAGMA table_info(options_prices)")
        columns = cursor.fetchall()
        print("\nOptions table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show sample records
        cursor.execute("SELECT * FROM options_prices LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("\nSample options records:")
            for row in rows:
                print(row)
    
    conn.close()
else:
    print(f"Database not found: {db_path}") 