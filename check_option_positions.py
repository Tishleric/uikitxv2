import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Check positions table for options
print('Checking positions table for options:')
cursor.execute("""
SELECT symbol, open_position, closed_position, fifo_realized_pnl, fifo_unrealized_pnl
FROM positions
WHERE symbol IN ('1MQ5C 111.75 Comdty', 'TJPQ25C1 110.5 Comdty', 'TYWQ25C1 112.5 Comdty')
   OR symbol LIKE '%MQ5C%' OR symbol LIKE '%TJPQ%' OR symbol LIKE '%TYWQ%'
""")

results = cursor.fetchall()
if results:
    for row in results:
        print(f'  {row[0]}: open={row[1]}, closed={row[2]}, realized_pnl={row[3]}, unrealized_pnl={row[4]}')
else:
    print('  NO OPTIONS FOUND IN POSITIONS TABLE!')

# Also check what symbols are in positions table
print('\nAll symbols in positions table:')
cursor.execute('SELECT symbol, open_position FROM positions ORDER BY symbol')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check what the aggregator sees
print('\nChecking trades_fifo for all symbols:')
cursor.execute("""
SELECT symbol, COUNT(*) as count, 
       SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as net_position
FROM trades_fifo
WHERE quantity > 0
GROUP BY symbol
""")
for row in cursor.fetchall():
    print(f'  {row[0]}: count={row[1]}, net={row[2]}')

conn.close()