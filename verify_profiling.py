"""Check if profiling data exists in observatory.db"""
import sqlite3

conn = sqlite3.connect('logs/observatory.db')
cursor = conn.cursor()

# Check for any profiling data
cursor.execute("""
    SELECT process, duration_ms, 
           CASE WHEN exception LIKE '%[PROFILE]%' THEN 'YES' ELSE 'NO' END as has_profile
    FROM process_trace
    ORDER BY ts DESC
    LIMIT 10
""")

print("Recent function calls:")
print(f"{'Function':<70} {'Duration':>10} {'Profiled'}")
print("-" * 85)

for row in cursor.fetchall():
    func = row[0] if len(row[0]) <= 70 else row[0][:67] + "..."
    print(f"{func:<70} {row[1]:>10.2f} {row[2]:>8}")

conn.close() 