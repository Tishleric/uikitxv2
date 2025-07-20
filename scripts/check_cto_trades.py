import sqlite3

conn = sqlite3.connect('../data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

# Check TYU5 and 3MN5P trades
cursor.execute("""
    SELECT Symbol, Type, Action, Quantity, Price 
    FROM cto_trades 
    WHERE Symbol LIKE '%TYU5%' OR Symbol LIKE '%3MN5%' 
    ORDER BY Symbol
""")
print('CTO Trades:')
for row in cursor.fetchall():
    print(f'  {row[0]} | Type={row[1]} | {row[2]} {row[3]} @ {row[4]}')

conn.close() 