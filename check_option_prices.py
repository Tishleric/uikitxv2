import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Check pricing table for options
cursor.execute("""
SELECT symbol, price_type, price, timestamp
FROM pricing
WHERE symbol IN ('1MQ5C 111.75 Comdty', 'TJPQ25C1 110.5 Comdty', 'TYWQ25C1 112.5 Comdty')
ORDER BY symbol, price_type
""")

print('Pricing table entries for options:')
results = cursor.fetchall()
if not results:
    print('  NO PRICES FOUND FOR OPTIONS!')
else:
    for row in results:
        print(f'  {row[0]}: {row[1]}={row[2]} ({row[3]})')

# Check all prices for TYU5 to compare
print('\nPricing table entries for TYU5 Comdty:')
cursor.execute("""
SELECT symbol, price_type, price, timestamp
FROM pricing
WHERE symbol = 'TYU5 Comdty'
ORDER BY price_type
""")
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}={row[2]} ({row[3]})')

# Check if there are any 'now' prices at all
cursor.execute("""
SELECT COUNT(*), COUNT(DISTINCT symbol) 
FROM pricing 
WHERE price_type = 'now'
""")
count, symbols = cursor.fetchone()
print(f'\nTotal "now" prices in system: {count} for {symbols} symbols')

# List all symbols with 'now' prices
cursor.execute("""
SELECT DISTINCT symbol 
FROM pricing 
WHERE price_type = 'now'
""")
print('\nSymbols with "now" prices:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')

conn.close()