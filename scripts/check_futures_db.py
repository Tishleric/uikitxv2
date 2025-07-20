import sqlite3

conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

cursor.execute('SELECT trade_date, symbol, Flash_Close, prior_close FROM futures_prices ORDER BY trade_date, symbol')
print('Futures prices in DB:')
for row in cursor.fetchall():
    print(f'  {row[0]} | {row[1]}: Flash={row[2]}, Prior={row[3]}')

# Check if we have July 18 TYU5 specifically
cursor.execute("SELECT trade_date, symbol, Flash_Close, prior_close FROM futures_prices WHERE trade_date = '2025-07-18' AND symbol = 'TYU5'")
result = cursor.fetchone()
if result:
    print(f"\nJuly 18 TYU5: Flash={result[2]}, Prior={result[3]}")
else:
    print("\nNo July 18 TYU5 data found!")

conn.close() 