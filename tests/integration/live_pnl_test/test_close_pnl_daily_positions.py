"""
Test that daily_positions only updates unrealized_pnl when today's close price exists.
"""

import sqlite3
import pytest
from datetime import datetime, timedelta
import pytz

from lib.trading.pnl_fifo_lifo import (
    create_all_tables,
    update_daily_position
)
from lib.trading.pnl_fifo_lifo.data_manager import update_daily_positions_unrealized_pnl


class TestClosePnLDailyPositions:
    """Test Close PnL behavior in daily_positions table"""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a test database"""
        db_path = tmp_path / "test_trades.db"
        conn = sqlite3.connect(str(db_path))
        create_all_tables(conn)
        yield conn
        conn.close()
    
    def setup_test_position(self, conn):
        """Setup a test position and daily position entry"""
        cursor = conn.cursor()
        
        # Insert a test trade
        cursor.execute("""
            INSERT INTO trades_fifo (
                transactionId, symbol, quantity, price, original_price,
                buySell, sequenceId, time, original_time, fullPartial
            ) VALUES (1, 'TYU5 Comdty', 10, 112.125, 112.125, 'B', 
                     'SEQ000001', '2025-08-05 09:30:00', '2025-08-05 09:30:00', 'full')
        """)
        
        # Create daily position entry
        today = datetime.now().strftime('%Y-%m-%d')
        update_daily_position(conn, today, 'TYU5 Comdty', 'fifo', 
                            realized_qty=0, realized_pnl_delta=0, accumulate=False)
        
        conn.commit()
    
    def test_no_update_without_todays_close(self, test_db):
        """Test that unrealized_pnl stays 0 when no today's close price"""
        conn = test_db
        self.setup_test_position(conn)
        
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Insert yesterday's close price
        cursor.execute("""
            INSERT INTO pricing (symbol, price_type, price, timestamp)
            VALUES ('TYU5 Comdty', 'close', 112.250, ?)
        """, (yesterday + ' 14:00:00',))
        conn.commit()
        
        # Run update
        update_daily_positions_unrealized_pnl(conn)
        
        # Check that unrealized_pnl is still 0
        result = cursor.execute("""
            SELECT unrealized_pnl FROM daily_positions 
            WHERE date = ? AND symbol = 'TYU5 Comdty' AND method = 'fifo'
        """, (today,)).fetchone()
        
        assert result is not None
        assert result[0] == 0.0, "Unrealized P&L should remain 0 without today's close"
    
    def test_update_with_todays_close(self, test_db):
        """Test that unrealized_pnl updates when today's close price exists"""
        conn = test_db
        self.setup_test_position(conn)
        
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Insert today's close price
        cursor.execute("""
            INSERT INTO pricing (symbol, price_type, price, timestamp)
            VALUES ('TYU5 Comdty', 'close', 112.250, ?)
        """, (today + ' 14:00:00',))
        conn.commit()
        
        # Run update
        update_daily_positions_unrealized_pnl(conn)
        
        # Check that unrealized_pnl was calculated
        # Expected: (112.250 - 112.125) * 10 * 1000 = 1250
        result = cursor.execute("""
            SELECT unrealized_pnl FROM daily_positions 
            WHERE date = ? AND symbol = 'TYU5 Comdty' AND method = 'fifo'
        """, (today,)).fetchone()
        
        assert result is not None
        assert result[0] == 1250.0, f"Expected 1250, got {result[0]}"
    
    def test_mixed_close_prices(self, test_db):
        """Test with mix of today's and old close prices"""
        conn = test_db
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
                # Setup two positions
        for idx, symbol in enumerate(['TYU5 Comdty', 'ZNU5 Comdty']):
            cursor.execute("""
                INSERT INTO trades_fifo (
                    transactionId, symbol, quantity, price, original_price, 
                    buySell, sequenceId, time, original_time, fullPartial
                ) VALUES (?, ?, 10, 112.125, 112.125, 'B', 
                         ?, '2025-08-05 09:30:00', '2025-08-05 09:30:00', 'full')
            """, (idx + 1, symbol, f'SEQ{idx + 1:06d}'))
            
            update_daily_position(conn, today, symbol, 'fifo', 0, 0, False)
        
        # TYU5 gets today's close, ZNU5 gets yesterday's
        cursor.execute("""
            INSERT INTO pricing (symbol, price_type, price, timestamp)
            VALUES ('TYU5 Comdty', 'close', 112.250, ?),
                   ('ZNU5 Comdty', 'close', 112.375, ?)
        """, (today + ' 14:00:00', yesterday + ' 14:00:00'))
        conn.commit()
        
        # Run update
        update_daily_positions_unrealized_pnl(conn)
        
        # Check results
        tyu5_result = cursor.execute("""
            SELECT unrealized_pnl FROM daily_positions 
            WHERE date = ? AND symbol = 'TYU5 Comdty' AND method = 'fifo'
        """, (today,)).fetchone()
        
        znu5_result = cursor.execute("""
            SELECT unrealized_pnl FROM daily_positions 
            WHERE date = ? AND symbol = 'ZNU5 Comdty' AND method = 'fifo'
        """, (today,)).fetchone()
        
        assert tyu5_result[0] == 1250.0, "TYU5 should have unrealized P&L with today's close"
        assert znu5_result[0] == 0.0, "ZNU5 should have 0 unrealized P&L with yesterday's close"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])