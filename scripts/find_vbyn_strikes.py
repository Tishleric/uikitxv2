import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
c = conn.cursor()

# Find all VBYN options with 110.750 strike
c.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE 'VBYN%' 
    AND bloomberg LIKE '%110.750%'
""")

print("VBYN options with 110.750 strike:")
for r in c.fetchall():
    print(f"  {r[0]}")

# Check what VBYN strikes exist around 110-111
print("\nAll VBYN strikes between 110-111:")
c.execute("""
    SELECT DISTINCT bloomberg 
    FROM market_prices 
    WHERE bloomberg LIKE 'VBYN%' 
    AND (bloomberg LIKE '%110%' OR bloomberg LIKE '%111%')
    ORDER BY bloomberg
    LIMIT 20
""")

for r in c.fetchall():
    print(f"  {r[0]}")

conn.close() 