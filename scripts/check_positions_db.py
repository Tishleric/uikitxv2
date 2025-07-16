import sqlite3

# Connect to the database
conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check positions count
cursor.execute('SELECT COUNT(*) as count FROM positions')
print(f'Position count: {cursor.fetchone()["count"]}')

# Get sample positions
cursor.execute('SELECT * FROM positions LIMIT 5')
rows = cursor.fetchall()

print('\nSample positions:')
for row in rows:
    print(dict(row))
    
# Check if last_market_price is populated
cursor.execute('SELECT COUNT(*) as count FROM positions WHERE last_market_price IS NOT NULL')
print(f'\nPositions with market prices: {cursor.fetchone()["count"]}')

conn.close() 