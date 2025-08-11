"""
Test Positions Aggregator with Close PnL Calculation
Parallel implementation that calculates both live and close unrealized PnL
"""

import sqlite3
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from lib.trading.pnl_fifo_lifo.data_manager import load_pricing_dictionaries, view_unrealized_positions
from lib.trading.pnl_fifo_lifo.pnl_engine import calculate_unrealized_pnl
from lib.trading.pnl_fifo_lifo.config import PNL_MULTIPLIER


class TestPositionsAggregator:
    """Test version of PositionsAggregator with close PnL calculation"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.positions_cache = pd.DataFrame()
        
    def load_and_calculate_positions(self):
        """Load positions and calculate both live and close unrealized PnL"""
        
        conn = sqlite3.connect(self.db_path)
        start_time = time.time()
        
        try:
            # Get current trading day
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Load base position data
            query = """
            WITH position_summary AS (
                SELECT 
                    symbol,
                    SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as open_position
                FROM trades_fifo
                WHERE quantity > 0
                GROUP BY symbol
            ),
            daily_summary AS (
                SELECT 
                    symbol,
                    MAX(CASE WHEN method = 'fifo' THEN realized_pnl END) as fifo_realized_pnl,
                    MAX(CASE WHEN method = 'lifo' THEN realized_pnl END) as lifo_realized_pnl,
                    MAX(CASE WHEN method = 'fifo' THEN closed_position END) as closed_position
                FROM daily_positions
                WHERE date = ?
                GROUP BY symbol
            )
            SELECT 
                COALESCE(p.symbol, d.symbol) as symbol,
                COALESCE(p.open_position, 0) as open_position,
                COALESCE(d.closed_position, 0) as closed_position,
                COALESCE(d.fifo_realized_pnl, 0) as fifo_realized_pnl,
                COALESCE(d.lifo_realized_pnl, 0) as lifo_realized_pnl
            FROM position_summary p
            FULL OUTER JOIN daily_summary d ON p.symbol = d.symbol
            """
            
            self.positions_cache = pd.read_sql_query(query, conn, params=(today,))
            
            # Initialize columns
            self.positions_cache['fifo_unrealized_pnl'] = 0.0
            self.positions_cache['lifo_unrealized_pnl'] = 0.0
            self.positions_cache['fifo_unrealized_pnl_close'] = 0.0
            self.positions_cache['lifo_unrealized_pnl_close'] = 0.0
            
            # Load all pricing data
            all_price_dicts = load_pricing_dictionaries(conn)
            
            # Calculate unrealized PnL for both live and close
            for method in ['fifo', 'lifo']:
                positions_df = view_unrealized_positions(conn, method)
                
                if not positions_df.empty:
                    for symbol in positions_df['symbol'].unique():
                        symbol_positions = positions_df[positions_df['symbol'] == symbol]
                        
                        # Calculate LIVE unrealized PnL
                        unrealized_live_list = calculate_unrealized_pnl(
                            symbol_positions, all_price_dicts, 'live'
                        )
                        total_unrealized_live = sum(u['unrealizedPnL'] for u in unrealized_live_list)
                        
                        # Calculate CLOSE unrealized PnL
                        # First check if we have today's close price
                        close_price_query = """
                        SELECT price, timestamp 
                        FROM pricing 
                        WHERE symbol = ? AND price_type = 'close'
                        """
                        close_result = conn.execute(close_price_query, (symbol,)).fetchone()
                        
                        total_unrealized_close = 0.0
                        has_todays_close = False
                        
                        if close_result:
                            close_timestamp = close_result[1]
                            # Check if close price is from today
                            if close_timestamp and close_timestamp.startswith(today):
                                has_todays_close = True
                                
                                # Create modified price dict with close price as 'now'
                                close_price_dicts = all_price_dicts.copy()
                                close_price_dicts['now'] = all_price_dicts.get('close', {}).copy()
                                
                                # Calculate unrealized with close prices
                                unrealized_close_list = calculate_unrealized_pnl(
                                    symbol_positions, close_price_dicts, 'live'
                                )
                                total_unrealized_close = sum(u['unrealizedPnL'] for u in unrealized_close_list)
                        
                        # Update cache
                        mask = self.positions_cache['symbol'] == symbol
                        if mask.any():
                            self.positions_cache.loc[mask, f'{method}_unrealized_pnl'] = total_unrealized_live
                            if has_todays_close:
                                self.positions_cache.loc[mask, f'{method}_unrealized_pnl_close'] = total_unrealized_close
                            else:
                                # Set to NaN to indicate no today's close price
                                self.positions_cache.loc[mask, f'{method}_unrealized_pnl_close'] = float('nan')
            
            # Write to positions table
            self._write_positions_to_db(conn)
            
            load_time = time.time() - start_time
            print(f"Loaded and calculated {len(self.positions_cache)} positions in {load_time:.2f}s")
            
            return self.positions_cache
            
        finally:
            conn.close()
    
    def _write_positions_to_db(self, conn):
        """Write positions with both live and close unrealized PnL to database"""
        
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for _, row in self.positions_cache.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO positions (
                    symbol, open_position, closed_position,
                    fifo_realized_pnl, fifo_unrealized_pnl,
                    lifo_realized_pnl, lifo_unrealized_pnl,
                    fifo_unrealized_pnl_close, lifo_unrealized_pnl_close,
                    last_updated, last_trade_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['symbol'],
                row['open_position'],
                row['closed_position'],
                row['fifo_realized_pnl'],
                row['fifo_unrealized_pnl'],
                row['lifo_realized_pnl'],
                row['lifo_unrealized_pnl'],
                row['fifo_unrealized_pnl_close'] if pd.notna(row['fifo_unrealized_pnl_close']) else None,
                row['lifo_unrealized_pnl_close'] if pd.notna(row['lifo_unrealized_pnl_close']) else None,
                now,
                now
            ))
        
        conn.commit()
        print(f"Written {len(self.positions_cache)} positions to database")


if __name__ == "__main__":
    # Test the aggregator
    from test_data_setup import create_test_database, insert_test_data
    
    # Setup test database
    db_path = 'test_close_pnl.db'
    conn = create_test_database(db_path)
    expected_values = insert_test_data(conn)
    conn.close()
    
    # Run aggregator
    aggregator = TestPositionsAggregator(db_path)
    positions = aggregator.load_and_calculate_positions()
    
    print("\nPositions DataFrame:")
    print(positions[['symbol', 'open_position', 'fifo_realized_pnl', 
                    'fifo_unrealized_pnl', 'fifo_unrealized_pnl_close']])