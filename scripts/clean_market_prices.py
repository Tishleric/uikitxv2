"""Clean invalid market price entries from database."""

import sqlite3
import sys
sys.path.append('.')

print("=== CLEANING MARKET PRICES TABLE ===\n")

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

# First, let's see what we're dealing with
cursor.execute("SELECT COUNT(*) FROM market_prices")
total_before = cursor.fetchone()[0]
print(f"Total records before cleaning: {total_before}")

# Find invalid entries
cursor.execute("""
    SELECT COUNT(*) FROM market_prices 
    WHERE px_settle LIKE '%#N/A%' 
       OR px_last LIKE '%#N/A%'
       OR px_settle = '#N/A Requesting Data...'
       OR px_last = '#N/A Requesting Data...'
""")
invalid_count = cursor.fetchone()[0]
print(f"Invalid records found: {invalid_count}")

# Delete all invalid entries
if invalid_count > 0:
    cursor.execute("""
        DELETE FROM market_prices 
        WHERE px_settle LIKE '%#N/A%' 
           OR px_last LIKE '%#N/A%'
           OR px_settle = '#N/A Requesting Data...'
           OR px_last = '#N/A Requesting Data...'
    """)
    conn.commit()
    print(f"Deleted {cursor.rowcount} invalid records")

# Also delete any records where both prices are NULL
cursor.execute("""
    DELETE FROM market_prices 
    WHERE px_settle IS NULL AND px_last IS NULL
""")
if cursor.rowcount > 0:
    conn.commit()
    print(f"Deleted {cursor.rowcount} records with no prices")

# Clear the entire table for a fresh start
print("\nClearing entire market_prices table for fresh import...")
cursor.execute("DELETE FROM market_prices")
conn.commit()
print(f"Cleared {cursor.rowcount} records")

cursor.execute("SELECT COUNT(*) FROM market_prices")
total_after = cursor.fetchone()[0]
print(f"\nTotal records after cleaning: {total_after}")

conn.close()
print("\n✓ Market prices table cleaned!") 