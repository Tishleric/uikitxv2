import sqlite3

conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check for ZN3 options (Bloomberg format)
cursor.execute("""
    SELECT symbol, Flash_Close, trade_date 
    FROM options_prices 
    WHERE symbol LIKE '%ZN3%' 
    ORDER BY symbol 
    LIMIT 20
""")
print('ZN3 options in market prices:')
for row in cursor.fetchall():
    print(f'  {row[0]}: Flash={row[1]}, Date={row[2]}')

# Check for 3MN5 pattern
cursor.execute("""
    SELECT symbol, Flash_Close, trade_date 
    FROM options_prices 
    WHERE symbol LIKE '%3MN5%' 
    ORDER BY symbol 
    LIMIT 20
""")
print('\n3MN5 options in market prices:')
for row in cursor.fetchall():
    print(f'  {row[0]}: Flash={row[1]}, Date={row[2]}')

# Look for specific strikes
cursor.execute("""
    SELECT symbol, Flash_Close, trade_date 
    FROM options_prices 
    WHERE symbol LIKE '%110.250%' OR symbol LIKE '%110.000%'
    ORDER BY symbol 
    LIMIT 20
""")
print('\nOptions with strikes 110.250 or 110.000:')
for row in cursor.fetchall():
    print(f'  {row[0]}: Flash={row[1]}, Date={row[2]}')

conn.close() 