"""Check what strikes are available for VBYN25C2 options."""

import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

print("VBYN25C2 options with strikes around 110-111:")
print("=" * 50)

cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE 'VBYN25C2%' 
    AND (bloomberg LIKE '%110%' OR bloomberg LIKE '%111%')
    ORDER BY bloomberg
""")

for row in cursor.fetchall():
    print(f"  {row[0]}")

print("\n\nChecking if VBYN25C2 110.750 exists specifically:")
cursor.execute("""
    SELECT COUNT(*) 
    FROM market_prices 
    WHERE bloomberg = 'VBYN25C2 110.750 Comdty'
""")
count = cursor.fetchone()[0]
print(f"  Found {count} records")

print("\n\nChecking all VBYN25C2 strikes:")
cursor.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE 'VBYN25C2%'
    ORDER BY bloomberg
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close() 