import sqlite3
conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Count rows in daily_positions
count = cursor.execute("SELECT COUNT(*) FROM daily_positions").fetchone()[0]
print(f"Daily positions rows: {count}")

if count > 0:
    # Show a sample
    rows = cursor.execute("SELECT * FROM daily_positions LIMIT 5").fetchall()
    for row in rows:
        print(row)
else:
    print("Daily positions table is EMPTY")
    
    # Check if other tables have data
    for table in ['trades_fifo', 'trades_lifo', 'realized_fifo', 'realized_lifo']:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows")

conn.close() 