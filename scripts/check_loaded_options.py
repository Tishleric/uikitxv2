"""Check what options were actually loaded into market_prices."""

import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

# Check total records
cursor.execute("SELECT COUNT(*) FROM market_prices")
total = cursor.fetchone()[0]
print(f"Total market_prices records: {total}")

# Check by asset type
cursor.execute("SELECT asset_type, COUNT(*) FROM market_prices GROUP BY asset_type")
print("\nRecords by asset type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check option patterns
print("\nOption symbol patterns (first 4 chars):")
cursor.execute("""
    SELECT SUBSTR(bloomberg, 1, 4) as pattern, COUNT(*) as count
    FROM market_prices 
    WHERE asset_type = 'OPTION'
    GROUP BY pattern
    ORDER BY count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} records")

# Check specific VBY options
print("\nVBY options:")
cursor.execute("""
    SELECT COUNT(*) 
    FROM market_prices 
    WHERE bloomberg LIKE 'VBY%'
""")
vby_count = cursor.fetchone()[0]
print(f"  Total VBY options: {vby_count}")

# Show sample option symbols
print("\nSample option symbols:")
cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE asset_type = 'OPTION'
    ORDER BY bloomberg
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check upload timestamps
print("\nUpload timestamps (latest 5):")
cursor.execute("""
    SELECT DISTINCT upload_timestamp 
    FROM market_prices 
    ORDER BY upload_timestamp DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close() 