import sqlite3

conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check options data summary
cursor.execute("""
    SELECT 
        trade_date, 
        COUNT(*) as total,
        SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as with_flash,
        SUM(CASE WHEN Flash_Close IS NULL THEN 1 ELSE 0 END) as without_flash
    FROM options_prices 
    WHERE trade_date >= '2025-07-17' 
    GROUP BY trade_date
    ORDER BY trade_date
""")

print("Options data summary:")
print("Date       | Total | With Flash | Without Flash")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]:5} | {row[2]:10} | {row[3]:13}")

# Check specific 3MN5P options on July 18
print("\n3MN5P options on July 18:")
cursor.execute("""
    SELECT symbol, Flash_Close, prior_close 
    FROM options_prices 
    WHERE trade_date = '2025-07-18' 
    AND symbol LIKE '3MN5P%'
    ORDER BY symbol
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: Flash={row[1]}, Prior={row[2]}")

conn.close() 