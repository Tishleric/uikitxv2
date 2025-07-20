import sqlite3

conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check options data for July 18
cursor.execute("""
    SELECT COUNT(*) FROM options_prices 
    WHERE trade_date = '2025-07-18' AND Flash_Close IS NOT NULL
""")
flash_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM options_prices 
    WHERE trade_date = '2025-07-18' AND Flash_Close IS NULL
""")
null_count = cursor.fetchone()[0]

print(f"July 18 Options:")
print(f"  With Flash_Close: {flash_count}")
print(f"  Without Flash_Close: {null_count}")

# Check a sample of 3MN5P options
cursor.execute("""
    SELECT symbol, Flash_Close, prior_close 
    FROM options_prices 
    WHERE trade_date = '2025-07-18' 
    AND symbol LIKE '3MN5P%'
    LIMIT 5
""")
print("\n3MN5P options on July 18:")
for row in cursor.fetchall():
    print(f"  {row[0]}: Flash={row[1]}, Prior={row[2]}")

conn.close() 