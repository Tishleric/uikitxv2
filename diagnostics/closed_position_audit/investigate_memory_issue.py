"""
Investigate if the issue was caused by watchers with stale memory/cache
"""
import sqlite3
import pandas as pd
from datetime import datetime

def investigate_memory_issue(db_path='../../trades.db'):
    """Deep dive into how trades were processed multiple times"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("INVESTIGATING MEMORY/CACHING ISSUE")
    print("=" * 80)
    
    # 1. Look at the realization timeline for trade 478
    print("\n### 1. DETAILED TIMELINE OF TRADE 478 REALIZATIONS ###")
    
    query = """
    SELECT 
        timestamp,
        symbol,
        sequenceIdBeingOffset,
        quantity,
        realizedPnL
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY timestamp
    """
    
    timeline = pd.read_sql_query(query, conn)
    
    if not timeline.empty:
        print("\nChronological order of realizations:")
        print(timeline.to_string(index=False))
        
        # Calculate time gaps
        timeline['timestamp'] = pd.to_datetime(timeline['timestamp'])
        timeline['time_gap'] = timeline['timestamp'].diff()
        
        print("\n### 2. TIME GAPS BETWEEN REALIZATIONS ###")
        gaps = timeline[timeline['time_gap'].notna()][['timestamp', 'symbol', 'time_gap']]
        print(gaps.to_string(index=False))
    
    # 3. Check if there are patterns in the processing
    print("\n### 3. PROCESSING PATTERNS ###")
    
    # Look for bursts of activity
    query = """
    SELECT 
        DATE(timestamp) as date,
        strftime('%H', timestamp) as hour,
        COUNT(*) as realizations,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols
    FROM realized_fifo
    WHERE DATE(timestamp) >= DATE('now', '-7 days')
    GROUP BY DATE(timestamp), strftime('%H', timestamp)
    HAVING COUNT(*) > 10
    ORDER BY date, hour
    """
    
    bursts = pd.read_sql_query(query, conn)
    
    if not bursts.empty:
        print("\nHigh-activity periods (>10 realizations per hour):")
        print(bursts.to_string(index=False))
    
    # 4. Check if positions_aggregator might be involved
    print("\n### 4. POSITIONS TABLE UPDATE PATTERNS ###")
    
    query = """
    SELECT 
        symbol,
        last_updated,
        last_trade_update,
        open_position,
        closed_position
    FROM positions
    WHERE symbol IN ('USU5 Comdty', 'TYU5 Comdty', 'TYWQ25C1 112.25 Comdty')
    """
    
    positions = pd.read_sql_query(query, conn)
    
    if not positions.empty:
        print("\nCurrent positions table state:")
        print(positions.to_string(index=False))
    
    # 5. Theory: Check if the issue correlates with specific files being processed
    print("\n### 5. FILE PROCESSING CORRELATION ###")
    
    query = """
    SELECT 
        file_path,
        processed_at,
        trade_count
    FROM processed_files
    WHERE DATE(processed_at) >= DATE('now', '-7 days')
    ORDER BY processed_at
    """
    
    files = pd.read_sql_query(query, conn)
    
    if not files.empty:
        print("\nFiles processed in the last 7 days:")
        for _, row in files.iterrows():
            print(f"  {row['processed_at']}: {row['file_path']} ({row['trade_count']} trades)")
    
    # 6. Look for evidence of duplicate trade processing
    print("\n### 6. DUPLICATE SEQUENCE ID PATTERNS ###")
    
    query = """
    WITH duplicate_realizations AS (
        SELECT 
            sequenceIdDoingOffsetting,
            COUNT(*) as times_used,
            COUNT(DISTINCT symbol) as symbols_offset,
            COUNT(DISTINCT sequenceIdBeingOffset) as positions_offset,
            MIN(timestamp) as first_use,
            MAX(timestamp) as last_use
        FROM realized_fifo
        GROUP BY sequenceIdDoingOffsetting
        HAVING COUNT(*) > 5
    )
    SELECT * FROM duplicate_realizations
    ORDER BY times_used DESC
    LIMIT 20
    """
    
    duplicates = pd.read_sql_query(query, conn)
    
    if not duplicates.empty:
        print("\nTrades used to offset many positions:")
        print(duplicates.to_string(index=False))
    
    conn.close()


def check_redis_state():
    """Check if Redis might have stale data"""
    print("\n" + "=" * 80)
    print("CHECKING REDIS STATE")
    print("=" * 80)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Check if Redis is running
        r.ping()
        print("\nRedis is running")
        
        # Check for any keys related to positions
        keys = r.keys('*position*')
        if keys:
            print(f"\nFound {len(keys)} position-related keys in Redis:")
            for key in keys[:10]:  # Show first 10
                print(f"  {key}")
        else:
            print("\nNo position-related keys found in Redis")
            
    except Exception as e:
        print(f"\nRedis check failed: {e}")
        print("This is normal if Redis is not running")


if __name__ == "__main__":
    investigate_memory_issue()
    check_redis_state()