"""
Diagnostic Script: Timeline analysis of position changes
This will help identify when the double-counting started
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def analyze_timeline(db_path='trades.db'):
    """Analyze when position discrepancies started appearing"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("TIMELINE ANALYSIS - CLOSED POSITION TRACKING")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # First, let's see the daily_positions growth over time
    print("### Daily Positions Growth Pattern ###")
    
    growth_query = """
    SELECT 
        date,
        symbol,
        method,
        closed_position,
        LAG(closed_position, 1, 0) OVER (PARTITION BY symbol, method ORDER BY date) as prev_closed,
        closed_position - LAG(closed_position, 1, 0) OVER (PARTITION BY symbol, method ORDER BY date) as daily_increase
    FROM daily_positions
    WHERE date >= DATE('now', '-10 days')
    ORDER BY symbol, method, date
    """
    
    growth_df = pd.read_sql_query(growth_query, conn)
    
    # Identify unusual spikes
    avg_daily_increase = growth_df[growth_df['daily_increase'] > 0]['daily_increase'].median()
    unusual_increases = growth_df[growth_df['daily_increase'] > avg_daily_increase * 2]
    
    if len(unusual_increases) > 0:
        print(f"\n⚠️  Found {len(unusual_increases)} unusual position increases (>2x median)")
        print("\nUnusual increases:")
        print("-" * 100)
        print(f"{'Date':<12} {'Symbol':<15} {'Method':<8} {'Previous':<10} {'Current':<10} {'Increase':<10}")
        print("-" * 100)
        
        for idx, row in unusual_increases.iterrows():
            print(f"{row['date']:<12} {row['symbol']:<15} {row['method']:<8} "
                  f"{row['prev_closed']:>10.0f} {row['closed_position']:>10.0f} "
                  f"{row['daily_increase']:>10.0f}")
    
    # Check realized trades insertion patterns
    print("\n### Realized Trades Insertion Timeline ###")
    
    for method in ['fifo', 'lifo']:
        insertion_query = f"""
        SELECT 
            DATE(timestamp) as trade_date,
            strftime('%Y-%m-%d %H:%M', timestamp) as trade_time,
            symbol,
            quantity,
            sequenceIdBeingOffset,
            sequenceIdDoingOffsetting
        FROM realized_{method}
        WHERE DATE(timestamp) >= DATE('now', '-5 days')
        ORDER BY timestamp DESC
        LIMIT 100
        """
        
        insertions = pd.read_sql_query(insertion_query, conn)
        
        # Group by hour to see if there are bursts of activity
        if len(insertions) > 0:
            insertions['hour'] = pd.to_datetime(insertions['trade_time']).dt.floor('H')
            hourly_summary = insertions.groupby(['trade_date', 'hour']).size().reset_index(name='trade_count')
            
            print(f"\n{method.upper()} - Recent trade insertion patterns:")
            
            # Check for duplicate-looking trades (same IDs within short time)
            potential_dupes = insertions.groupby(['sequenceIdBeingOffset', 'sequenceIdDoingOffsetting']).size()
            dupes = potential_dupes[potential_dupes > 1]
            
            if len(dupes) > 0:
                print(f"\n⚠️  Found {len(dupes)} trade ID pairs inserted multiple times recently!")
                
                for (offset_id, offsetting_id), count in dupes.items():
                    trades = insertions[
                        (insertions['sequenceIdBeingOffset'] == offset_id) & 
                        (insertions['sequenceIdDoingOffsetting'] == offsetting_id)
                    ]
                    print(f"\nTrade {offset_id} -> {offsetting_id} appears {count} times:")
                    print(trades[['trade_time', 'symbol', 'quantity']].to_string(index=False))
    
    # Check if close PnL columns exist and when they were populated
    print("\n### Close PnL Implementation Check ###")
    
    try:
        close_pnl_query = """
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN fifo_unrealized_pnl_close != 0 THEN 1 ELSE 0 END) as rows_with_close_pnl,
            MIN(CASE WHEN fifo_unrealized_pnl_close != 0 THEN last_updated ELSE NULL END) as first_close_pnl_update,
            MAX(last_updated) as most_recent_update
        FROM positions
        """
        close_pnl_info = pd.read_sql_query(close_pnl_query, conn)
        
        print("\nClose PnL column status:")
        print(close_pnl_info.to_string(index=False))
        
    except sqlite3.OperationalError as e:
        if "no such column" in str(e):
            print("\n❌ Close PnL columns not found - implementation may not be deployed")
        else:
            print(f"\n❌ Error checking close PnL: {e}")
    
    # Check processed files to see if any were re-processed
    print("\n### Processed Files Check ###")
    
    files_query = """
    SELECT 
        filename,
        line_count,
        processed_at,
        LAG(processed_at, 1) OVER (PARTITION BY filename ORDER BY processed_at) as prev_processed
    FROM processed_files
    WHERE processed_at >= datetime('now', '-2 days')
    ORDER BY processed_at DESC
    """
    
    files_df = pd.read_sql_query(files_query, conn)
    
    # Check for files processed multiple times
    duplicate_files = files_df[files_df.duplicated(subset=['filename'], keep=False)]
    
    if len(duplicate_files) > 0:
        print(f"\n⚠️  Found {len(duplicate_files)//2} files processed multiple times!")
        print("\nRe-processed files:")
        print(duplicate_files[['filename', 'processed_at', 'line_count']].to_string(index=False))
    else:
        print("\n✅ No files were re-processed recently")
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_timeline()