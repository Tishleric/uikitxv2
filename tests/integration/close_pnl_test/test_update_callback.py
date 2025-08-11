"""
Test Update Callback for FRGMonitor
Simulates the positions table update logic with close PnL
"""

import sqlite3
import pandas as pd
from datetime import datetime
import pytz
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Chicago timezone
CHICAGO_TZ = pytz.timezone('America/Chicago')


def test_update_positions_table(db_path='test_close_pnl.db'):
    """
    Test version of update_positions_table callback
    Fetches positions with both live and close PnL
    """
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Get current Chicago time
        now_cdt = datetime.now(CHICAGO_TZ)
        today_str = now_cdt.strftime('%Y-%m-%d')
        
        # Main query - includes both live and close PnL
        query = """
        SELECT 
            p.symbol,
            p.instrument_type,
            p.open_position,
            p.closed_position,
            p.delta_y,
            p.gamma_y,
            p.speed_y,
            p.theta,
            (p.theta / 252.0) as theta_decay_pnl,
            p.vega,
            p.fifo_realized_pnl,
            p.fifo_unrealized_pnl,
            (p.fifo_realized_pnl + p.fifo_unrealized_pnl) as pnl_live,
            p.lifo_realized_pnl,
            p.lifo_unrealized_pnl,
            CASE WHEN p.instrument_type = 'FUTURE' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS non_gamma_lifo,
            CASE WHEN p.instrument_type = 'OPTION' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS gamma_lifo,
            p.last_updated,
            pr_now.price as live_px,
            pr_close.price as close_px,
            -- NEW: Check if close price is from today
            CASE 
                WHEN pr_close.timestamp LIKE ? || '%' THEN pr_close.price 
                ELSE NULL 
            END as close_px_today,
            -- NEW: Close PnL calculation
            CASE 
                WHEN pr_close.timestamp LIKE ? || '%' THEN (p.fifo_realized_pnl + p.fifo_unrealized_pnl_close)
                ELSE NULL 
            END as pnl_close
        FROM positions p
        LEFT JOIN pricing pr_now ON p.symbol = pr_now.symbol AND pr_now.price_type = 'now'
        LEFT JOIN pricing pr_close ON p.symbol = pr_close.symbol AND pr_close.price_type = 'close'
        WHERE p.open_position != 0 OR p.closed_position != 0
        ORDER BY p.symbol
        """
        
        df = pd.read_sql_query(query, conn, params=(today_str, today_str))
        conn.close()
        
        # Convert to records for display
        data = df.to_dict('records')
        
        # Print results
        print(f"\nPositions as of {now_cdt.strftime('%Y-%m-%d %H:%M:%S')} Chicago time:")
        print("-" * 100)
        print(f"{'Symbol':<15} {'Open':<8} {'Live PnL':<12} {'Close PnL':<12} {'Close PX':<10} {'Note':<30}")
        print("-" * 100)
        
        for row in data:
            symbol = row['symbol']
            open_pos = row['open_position']
            pnl_live = row['pnl_live']
            pnl_close = row['pnl_close']
            close_px_today = row['close_px_today']
            
            # Format values
            pnl_live_str = f"${pnl_live:,.2f}" if pnl_live else "$0.00"
            
            if pnl_close is not None:
                pnl_close_str = f"${pnl_close:,.2f}"
                note = "Today's close available"
            else:
                pnl_close_str = "NULL"
                note = "No today's close price"
            
            close_px_str = f"{close_px_today:.3f}" if close_px_today else "N/A"
            
            print(f"{symbol:<15} {open_pos:<8.0f} {pnl_live_str:<12} {pnl_close_str:<12} {close_px_str:<10} {note:<30}")
        
        print("-" * 100)
        
        return data
        
    except Exception as e:
        print(f"Error in test update callback: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_close_price_availability(db_path='test_close_pnl.db'):
    """Test the logic for determining close price availability"""
    
    conn = sqlite3.connect(db_path)
    today_str = datetime.now(CHICAGO_TZ).strftime('%Y-%m-%d')
    
    # Check which symbols have today's close prices
    query = """
    SELECT 
        symbol, 
        price,
        timestamp,
        CASE WHEN timestamp LIKE ? || '%' THEN 1 ELSE 0 END as is_today
    FROM pricing 
    WHERE price_type = 'close'
    ORDER BY symbol
    """
    
    df = pd.read_sql_query(query, conn, params=(today_str,))
    conn.close()
    
    print("\nClose Price Availability:")
    print("-" * 60)
    print(f"{'Symbol':<20} {'Price':<10} {'Timestamp':<20} {'Is Today?':<10}")
    print("-" * 60)
    
    for _, row in df.iterrows():
        is_today_str = "YES" if row['is_today'] else "NO"
        print(f"{row['symbol']:<20} {row['price']:<10.3f} {row['timestamp']:<20} {is_today_str:<10}")
    
    return df


if __name__ == "__main__":
    # First check close price availability
    test_close_price_availability()
    
    # Then run the main callback test
    test_update_positions_table()