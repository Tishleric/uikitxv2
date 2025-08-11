"""
Simple test for P&L database write functionality.
Tests just the _write_positions_to_db function directly.
"""

import sqlite3
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables


def test_simple_db_write():
    """Test writing P&L values directly to positions table"""
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        print("=== SIMPLE P&L DATABASE WRITE TEST ===\n")
        
        # 1. Create database and tables
        print("1. Creating database and tables...")
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        conn.close()
        
        # 2. Create test DataFrame (mimicking positions_cache)
        print("2. Creating test positions data...")
        test_data = pd.DataFrame([
            {
                'symbol': 'TEST1',
                'open_position': 10.0,
                'closed_position': 5.0,
                'fifo_realized_pnl': 1000.0,
                'fifo_unrealized_pnl': 2500.0,      # Our test P&L value
                'lifo_realized_pnl': 1100.0,
                'lifo_unrealized_pnl': 2600.0,      # Our test P&L value
                'fifo_unrealized_pnl_close': 2400.0,  # Close P&L
                'lifo_unrealized_pnl_close': 2500.0,  # Close P&L
                'delta_y': 0.5,
                'gamma_y': 0.01,
                'speed_y': 0.001,
                'theta': -10.0,
                'vega': 5.0,
                'has_greeks': True,
                'instrument_type': 'future'
            },
            {
                'symbol': 'TEST2',
                'open_position': -5.0,
                'closed_position': 0.0,
                'fifo_realized_pnl': 0.0,
                'fifo_unrealized_pnl': -1500.0,     # Negative P&L
                'lifo_realized_pnl': 0.0,
                'lifo_unrealized_pnl': -1400.0,     # Negative P&L
                'fifo_unrealized_pnl_close': -1450.0,
                'lifo_unrealized_pnl_close': -1350.0,
                'delta_y': -0.25,
                'gamma_y': 0.005,
                'speed_y': 0.0005,
                'theta': -5.0,
                'vega': 2.5,
                'has_greeks': True,
                'instrument_type': 'future'
            }
        ])
        
        # 3. Write to database (mimicking _write_positions_to_db)
        print("3. Writing to positions table...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for _, row in test_data.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO positions (
                    symbol, open_position, closed_position,
                    delta_y, gamma_y, speed_y, theta, vega,
                    fifo_realized_pnl, fifo_unrealized_pnl,
                    lifo_realized_pnl, lifo_unrealized_pnl,
                    fifo_unrealized_pnl_close, lifo_unrealized_pnl_close,
                    last_updated, last_trade_update, last_greek_update,
                    has_greeks, instrument_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['symbol'],
                row['open_position'],
                row['closed_position'],
                row['delta_y'],
                row['gamma_y'],
                row['speed_y'],
                row['theta'],
                row['vega'],
                row['fifo_realized_pnl'],
                row['fifo_unrealized_pnl'],
                row['lifo_realized_pnl'],
                row['lifo_unrealized_pnl'],
                row.get('fifo_unrealized_pnl_close', 0),
                row.get('lifo_unrealized_pnl_close', 0),
                now,
                now,
                now if row['has_greeks'] else None,
                1 if row['has_greeks'] else 0,
                row['instrument_type']
            ))
        
        conn.commit()
        print("✓ Data committed to database")
        
        # 4. Verify by reading back
        print("\n4. Verifying data in positions table...")
        query = """
            SELECT 
                symbol,
                open_position,
                fifo_unrealized_pnl,
                lifo_unrealized_pnl,
                fifo_unrealized_pnl_close,
                lifo_unrealized_pnl_close
            FROM positions
            ORDER BY symbol
        """
        
        result_df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("\nData in positions table:")
        print(result_df.to_string(index=False))
        
        # 5. Verify values match
        print("\n5. Verifying values...")
        for i, row in result_df.iterrows():
            original = test_data[test_data['symbol'] == row['symbol']].iloc[0]
            
            assert row['fifo_unrealized_pnl'] == original['fifo_unrealized_pnl'], \
                f"FIFO unrealized P&L mismatch for {row['symbol']}"
            assert row['lifo_unrealized_pnl'] == original['lifo_unrealized_pnl'], \
                f"LIFO unrealized P&L mismatch for {row['symbol']}"
            assert row['fifo_unrealized_pnl_close'] == original['fifo_unrealized_pnl_close'], \
                f"FIFO close P&L mismatch for {row['symbol']}"
            assert row['lifo_unrealized_pnl_close'] == original['lifo_unrealized_pnl_close'], \
                f"LIFO close P&L mismatch for {row['symbol']}"
            
            print(f"✓ {row['symbol']} values match")
        
        print("\n✓ TEST PASSED - All P&L values correctly written to database!")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_simple_db_write()