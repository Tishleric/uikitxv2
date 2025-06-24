import sqlite3
import sys
sys.path.insert(0, '.')

from lib.monitoring.decorators.monitor import get_observatory_queue, _batch_writer

print("=== Observatory System Diagnosis ===\n")

# 1. Check queue status
queue = get_observatory_queue()
print(f"1. Queue Status:")
print(f"   {queue.get_queue_stats()}")

# 2. Check batch writer
print(f"\n2. Batch Writer Status:")
if _batch_writer:
    print(f"   Writer exists: Yes")
    print(f"   Writer stats: {_batch_writer.get_stats()}")
else:
    print(f"   Writer exists: No (THIS IS THE PROBLEM)")

# 3. Check database directly
print(f"\n3. Database Check:")
conn = sqlite3.connect('logs/observatory.db')
cursor = conn.cursor()

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"   Tables: {[t[0] for t in tables]}")

# Count records
if tables:
    cursor.execute("SELECT COUNT(*) FROM process_trace")
    process_count = cursor.fetchone()[0]
    print(f"   Total process records: {process_count}")
    
    # Look for trading functions
    cursor.execute("""
        SELECT DISTINCT process 
        FROM process_trace 
        WHERE process LIKE '%trading%' OR process LIKE '%pricing_monkey%'
        ORDER BY process
    """)
    trading_funcs = cursor.fetchall()
    print(f"\n   Trading functions found: {len(trading_funcs)}")
    for func in trading_funcs:
        print(f"   - {func[0]}")
    
    # Check recent records
    print(f"\n   Most recent 5 records:")
    cursor.execute("""
        SELECT ts, process, status, duration_ms
        FROM process_trace
        ORDER BY ts DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} | {row[1]:<60} | {row[2]} | {row[3]:.1f}ms")

conn.close()

# 4. Try calling a function directly
print(f"\n4. Direct Function Test:")
from lib.monitoring.decorators.monitor import monitor

@monitor()
def test_trading_function():
    return "success"

print("   Calling test function...")
result = test_trading_function()
print(f"   Result: {result}")

# Wait for writer to flush
import time
time.sleep(1)

# Check if it was written
conn = sqlite3.connect('logs/observatory.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT COUNT(*) 
    FROM process_trace 
    WHERE process LIKE '%test_trading_function%'
""")
test_count = cursor.fetchone()[0]
print(f"   Test function in database: {'Yes' if test_count > 0 else 'No'}")
conn.close() 