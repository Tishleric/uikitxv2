import sqlite3

conn = sqlite3.connect('../data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM cto_trades WHERE source_file LIKE '%trades_20250717.csv'")
conn.commit()
print(f'Deleted {cursor.rowcount} rows')
conn.close() 