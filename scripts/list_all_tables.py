import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("All tables in pnl_tracker.db:")
for table in tables:
    print(f"  - {table[0]}")

# Check specifically for FULLPNL tables
fullpnl_tables = [t[0] for t in tables if 'FULLPNL' in t[0].upper()]
print(f"\nFULLPNL-related tables: {fullpnl_tables}")

conn.close() 