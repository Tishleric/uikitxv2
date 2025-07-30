"""View profiling results from the observatory database."""
import sqlite3
from datetime import datetime, timedelta

def view_profiling_results(minutes_back=10):
    """View recent profiling results from observatory.db"""
    
    conn = sqlite3.connect('logs/observatory.db')
    cursor = conn.cursor()
    
    # Calculate time threshold
    threshold = datetime.now() - timedelta(minutes=minutes_back)
    threshold_str = threshold.isoformat()
    
    print(f"\n=== Profiling Results from last {minutes_back} minutes ===\n")
    
    # Query for profiled functions (those with [PROFILE] in exception field and status OK)
    query = """
    SELECT ts, process, duration_ms, exception
    FROM process_trace
    WHERE ts > ? AND status = 'OK' AND exception LIKE '%[PROFILE]%'
    ORDER BY ts DESC
    """
    
    cursor.execute(query, (threshold_str,))
    results = cursor.fetchall()
    
    if not results:
        print("No profiling data found. Make sure MONITOR_PROFILING=1 is set.")
        
        # Show recent non-profiled entries for debugging
        print("\nRecent entries (without profiling):")
        cursor.execute("""
            SELECT ts, process, duration_ms, status
            FROM process_trace
            WHERE ts > ?
            ORDER BY ts DESC
            LIMIT 10
        """, (threshold_str,))
        
        for row in cursor.fetchall():
            print(f"{row[0]} | {row[1]} | {row[2]:.2f}ms | {row[3]}")
    else:
        for ts, process, duration_ms, profile_data in results:
            print(f"\n{'='*80}")
            print(f"Function: {process}")
            print(f"Time: {ts}")
            print(f"Total Duration: {duration_ms:.2f}ms")
            print(f"\nProfile Stats:")
            print("-" * 80)
            # Remove [PROFILE] prefix and print the stats
            stats = profile_data.replace('[PROFILE]\n', '')
            print(stats)
    
    # Also show summary of all functions by total time
    print(f"\n{'='*80}")
    print("Summary of all monitored functions (sorted by total time):")
    print("-" * 80)
    
    cursor.execute("""
        SELECT process, COUNT(*) as calls, 
               SUM(duration_ms) as total_ms, 
               AVG(duration_ms) as avg_ms,
               MIN(duration_ms) as min_ms,
               MAX(duration_ms) as max_ms
        FROM process_trace
        WHERE ts > ? AND status = 'OK'
        GROUP BY process
        ORDER BY total_ms DESC
        LIMIT 20
    """, (threshold_str,))
    
    print(f"{'Function':<60} {'Calls':>6} {'Total(ms)':>10} {'Avg(ms)':>10} {'Min(ms)':>10} {'Max(ms)':>10}")
    print("-" * 116)
    
    for row in cursor.fetchall():
        process = row[0] if len(row[0]) <= 60 else row[0][:57] + "..."
        print(f"{process:<60} {row[1]:>6} {row[2]:>10.2f} {row[3]:>10.2f} {row[4]:>10.2f} {row[5]:>10.2f}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    view_profiling_results(minutes) 