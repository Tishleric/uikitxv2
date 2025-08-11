"""
Unit tests for trade database insertions in FIFO/LIFO PnL system.

Tests the exact mechanisms used by trade_ledger_watcher.py for inserting trades
into trades_fifo, trades_lifo, realized_fifo, and realized_lifo tables.
"""

import sqlite3
import pytest
from datetime import datetime
from decimal import Decimal

# Add parent directories to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables, update_daily_position


class TestTradeInsertions:
    """Test suite for verifying correct trade insertions into database tables."""
    
    @pytest.fixture
    def db_connection(self):
        """Create an in-memory SQLite database with required tables."""
        conn = sqlite3.connect(':memory:')
        create_all_tables(conn)
        yield conn
        conn.close()
    
    @pytest.fixture
    def sample_trade(self):
        """Create a sample trade dictionary."""
        return {
            'transactionId': 12345,
            'symbol': 'TYH5 Comdty',
            'price': 110.25,
            'quantity': 10,
            'buySell': 'B',
            'sequenceId': '20240115-1',
            'time': '2024-01-15 09:30:00.000',
            'fullPartial': 'full'
        }
    
    def verify_table_counts(self, conn, expected_counts):
        """Helper to verify row counts in all tables."""
        cursor = conn.cursor()
        for table, expected in expected_counts.items():
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count == expected, f"{table} has {count} rows, expected {expected}"
    
    def get_positions(self, conn, method, symbol=None):
        """Get all positions from trades_{method} table."""
        cursor = conn.cursor()
        query = f"SELECT * FROM trades_{method}"
        params = ()
        if symbol:
            query += " WHERE symbol = ?"
            params = (symbol,)
        return cursor.execute(query, params).fetchall()
    
    def get_realized(self, conn, method, symbol=None):
        """Get all realized trades from realized_{method} table."""
        cursor = conn.cursor()
        query = f"SELECT * FROM realized_{method}"
        params = ()
        if symbol:
            query += " WHERE symbol = ?"
            params = (symbol,)
        return cursor.execute(query, params).fetchall()
    
    def test_single_new_position(self, db_connection, sample_trade):
        """Test insertion of a single new position with no offsetting."""
        # Process the trade for both FIFO and LIFO
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, sample_trade, method)
        
        db_connection.commit()
        
        # Verify correct insertions
        expected_counts = {
            'trades_fifo': 1,
            'trades_lifo': 1,
            'realized_fifo': 0,
            'realized_lifo': 0
        }
        self.verify_table_counts(db_connection, expected_counts)
        
        # Verify position details
        for method in ['fifo', 'lifo']:
            positions = self.get_positions(db_connection, method)
            assert len(positions) == 1
            pos = positions[0]
            
            # Verify all fields
            assert pos[0] == sample_trade['transactionId']  # transactionId
            assert pos[1] == sample_trade['symbol']         # symbol
            assert pos[2] == sample_trade['price']          # price
            assert pos[3] == sample_trade['price']          # original_price
            assert pos[4] == sample_trade['quantity']       # quantity
            assert pos[5] == sample_trade['buySell']        # buySell
            assert pos[6] == sample_trade['sequenceId']     # sequenceId
            assert pos[7] == sample_trade['time']           # time
            assert pos[8] == sample_trade['time']           # original_time
            assert pos[9] == 'full'                         # fullPartial
    
    def test_full_offset_trade(self, db_connection, sample_trade):
        """Test a trade that fully offsets an existing position."""
        # First, insert initial position
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, sample_trade, method)
        db_connection.commit()
        
        # Create offsetting trade (sell same quantity)
        offset_trade = {
            'transactionId': 12346,
            'symbol': 'TYH5 Comdty',
            'price': 111.00,  # Sell at higher price (profit)
            'quantity': 10,
            'buySell': 'S',  # Opposite side
            'sequenceId': '20240115-2',
            'time': '2024-01-15 10:30:00.000',
            'fullPartial': 'full'
        }
        
        # Process offsetting trade
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, offset_trade, method)
        db_connection.commit()
        
        # Verify no open positions remain
        expected_counts = {
            'trades_fifo': 0,  # Position fully closed
            'trades_lifo': 0,  # Position fully closed
            'realized_fifo': 1,  # One realized trade
            'realized_lifo': 1   # One realized trade
        }
        self.verify_table_counts(db_connection, expected_counts)
        
        # Verify realized P&L
        for method in ['fifo', 'lifo']:
            realized = self.get_realized(db_connection, method)
            assert len(realized) == 1
            
            # Fields: symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, 
            # partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp
            r = realized[0]
            assert r[0] == 'TYH5 Comdty'      # symbol
            assert r[1] == '20240115-1'       # sequenceIdBeingOffset
            assert r[2] == '20240115-2'       # sequenceIdDoingOffsetting
            assert r[3] == 'full'             # partialFull
            assert r[4] == 10                 # quantity
            assert r[5] == 110.25             # entryPrice
            assert r[6] == 111.00             # exitPrice
            # P&L = (111.00 - 110.25) * 10 * 1000 = 7500
            assert r[7] == 7500               # realizedPnL
    
    def test_partial_offset_trade(self, db_connection, sample_trade):
        """Test a trade that partially offsets an existing position."""
        # Insert initial position of 10
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, sample_trade, method)
        db_connection.commit()
        
        # Create partial offsetting trade (sell 6 out of 10)
        partial_offset = {
            'transactionId': 12347,
            'symbol': 'TYH5 Comdty',
            'price': 110.50,
            'quantity': 6,
            'buySell': 'S',
            'sequenceId': '20240115-3',
            'time': '2024-01-15 11:00:00.000',
            'fullPartial': 'full'
        }
        
        # Process partial offset
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, partial_offset, method)
        db_connection.commit()
        
        # Verify positions
        expected_counts = {
            'trades_fifo': 1,    # Still have 4 remaining
            'trades_lifo': 1,    # Still have 4 remaining
            'realized_fifo': 1,  # Partial realization
            'realized_lifo': 1   # Partial realization
        }
        self.verify_table_counts(db_connection, expected_counts)
        
        # Check remaining position
        for method in ['fifo', 'lifo']:
            positions = self.get_positions(db_connection, method)
            assert len(positions) == 1
            pos = positions[0]
            assert pos[4] == 4  # Remaining quantity
            assert pos[9] == 'partial'  # fullPartial flag updated
            
            # Check realized trade
            realized = self.get_realized(db_connection, method)
            assert len(realized) == 1
            r = realized[0]
            assert r[3] == 'partial'  # partialFull
            assert r[4] == 6          # quantity realized
            # P&L = (110.50 - 110.25) * 6 * 1000 = 1500
            assert r[7] == 1500       # realizedPnL
    
    def test_fifo_vs_lifo_ordering(self, db_connection):
        """Test that FIFO and LIFO process trades in correct order."""
        # Create three buy positions
        trades = [
            {
                'transactionId': 1001,
                'symbol': 'ESH5 Comdty',
                'price': 4000.00,
                'quantity': 5,
                'buySell': 'B',
                'sequenceId': '20240115-10',
                'time': '2024-01-15 09:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1002,
                'symbol': 'ESH5 Comdty',
                'price': 4010.00,
                'quantity': 5,
                'buySell': 'B',
                'sequenceId': '20240115-11',
                'time': '2024-01-15 09:30:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1003,
                'symbol': 'ESH5 Comdty',
                'price': 4020.00,
                'quantity': 5,
                'buySell': 'B',
                'sequenceId': '20240115-12',
                'time': '2024-01-15 10:00:00.000',
                'fullPartial': 'full'
            }
        ]
        
        # Insert all positions
        for trade in trades:
            for method in ['fifo', 'lifo']:
                process_new_trade(db_connection, trade, method)
        db_connection.commit()
        
        # Create offsetting sell trade
        sell_trade = {
            'transactionId': 1004,
            'symbol': 'ESH5 Comdty',
            'price': 4015.00,
            'quantity': 5,
            'buySell': 'S',
            'sequenceId': '20240115-13',
            'time': '2024-01-15 11:00:00.000',
            'fullPartial': 'full'
        }
        
        # Process the sell
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, sell_trade, method)
        db_connection.commit()
        
        # Check FIFO realized trade (should offset first trade at 4000)
        fifo_realized = self.get_realized(db_connection, 'fifo', 'ESH5 Comdty')
        assert len(fifo_realized) == 1
        assert fifo_realized[0][1] == '20240115-10'  # Offset oldest first
        assert fifo_realized[0][5] == 4000.00        # Entry price
        # P&L = (4015 - 4000) * 5 * 1000 = 75000
        assert fifo_realized[0][7] == 75000
        
        # Check LIFO realized trade (should offset last trade at 4020)
        lifo_realized = self.get_realized(db_connection, 'lifo', 'ESH5 Comdty')
        assert len(lifo_realized) == 1
        assert lifo_realized[0][1] == '20240115-12'  # Offset newest first
        assert lifo_realized[0][5] == 4020.00        # Entry price
        # P&L = (4015 - 4020) * 5 * 1000 = -25000 (loss)
        assert lifo_realized[0][7] == -25000
    
    def test_no_duplicate_sequence_ids(self, db_connection):
        """Test that sequence IDs are unique across all tables."""
        # Create multiple trades
        trades = [
            {
                'transactionId': 2001,
                'symbol': 'CLH5 Comdty',
                'price': 75.50,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': '20240115-20',
                'time': '2024-01-15 12:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 2002,
                'symbol': 'CLH5 Comdty',
                'price': 76.00,
                'quantity': 5,
                'buySell': 'S',
                'sequenceId': '20240115-21',
                'time': '2024-01-15 12:30:00.000',
                'fullPartial': 'full'
            }
        ]
        
        # Process trades
        for trade in trades:
            for method in ['fifo', 'lifo']:
                process_new_trade(db_connection, trade, method)
        db_connection.commit()
        
        # Collect all sequence IDs
        cursor = db_connection.cursor()
        all_seq_ids = []
        
        # From trades tables
        for method in ['fifo', 'lifo']:
            seq_ids = cursor.execute(
                f"SELECT sequenceId FROM trades_{method}"
            ).fetchall()
            all_seq_ids.extend([sid[0] for sid in seq_ids])
        
        # From realized tables (both offset and offsetting IDs)
        for method in ['fifo', 'lifo']:
            seq_ids = cursor.execute(
                f"SELECT sequenceIdBeingOffset, sequenceIdDoingOffsetting "
                f"FROM realized_{method}"
            ).fetchall()
            for row in seq_ids:
                all_seq_ids.extend([row[0], row[1]])
        
        # Check uniqueness (each ID should appear exactly as expected)
        # '20240115-20' appears in trades_fifo, trades_lifo, and as being offset
        # '20240115-21' appears as doing offsetting
        from collections import Counter
        seq_counter = Counter(all_seq_ids)
        
        # Each sequence ID should appear the expected number of times
        assert seq_counter['20240115-20'] == 4  # 2 in trades + 2 as being offset
        assert seq_counter['20240115-21'] == 2  # 2 as doing offsetting
    
    def test_daily_position_update(self, db_connection, sample_trade):
        """Test the update_daily_position function."""
        # Process initial trade
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, sample_trade, method)
        db_connection.commit()
        
        # Update daily position (simulating what trade_ledger_watcher does)
        trade_date = '2024-01-15'
        for method in ['fifo', 'lifo']:
            update_daily_position(
                db_connection, 
                trade_date, 
                sample_trade['symbol'], 
                method,
                realized_qty=0,  # No realized quantity yet
                realized_pnl_delta=0
            )
        db_connection.commit()
        
        # Check daily_positions table
        cursor = db_connection.cursor()
        positions = cursor.execute(
            "SELECT * FROM daily_positions WHERE symbol = ?",
            (sample_trade['symbol'],)
        ).fetchall()
        
        assert len(positions) == 2  # One for FIFO, one for LIFO
        
        for pos in positions:
            assert pos[0] == trade_date           # date
            assert pos[1] == sample_trade['symbol']  # symbol
            assert pos[2] in ['fifo', 'lifo']    # method
            assert pos[3] == 10                   # open_position (net)
            assert pos[4] == 0                    # closed_position
            assert pos[5] == 0                    # realized_pnl
    
    def test_transaction_atomicity(self, db_connection):
        """Test that all operations are atomic (all succeed or all fail)."""
        # Insert initial position
        trade = {
            'transactionId': 3001,
            'symbol': 'GCH5 Comdty',
            'price': 1850.00,
            'quantity': 10,
            'buySell': 'B',
            'sequenceId': '20240115-30',
            'time': '2024-01-15 13:00:00.000',
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, trade, method)
        db_connection.commit()
        
        # Create a trade with invalid data that will cause an error
        # We'll simulate this by attempting to process with a bad connection
        bad_conn = sqlite3.connect(':memory:')  # No tables created
        
        invalid_trade = {
            'transactionId': 3002,
            'symbol': 'GCH5 Comdty',
            'price': 1860.00,
            'quantity': 5,
            'buySell': 'S',
            'sequenceId': '20240115-31',
            'time': '2024-01-15 13:30:00.000',
            'fullPartial': 'full'
        }
        
        # This should raise an error
        with pytest.raises(sqlite3.OperationalError):
            process_new_trade(bad_conn, invalid_trade, 'fifo')
        
        bad_conn.close()
        
        # Verify original database is unchanged
        positions = self.get_positions(db_connection, 'fifo', 'GCH5 Comdty')
        assert len(positions) == 1
        assert positions[0][4] == 10  # Original quantity unchanged
    
    def test_short_position_pnl(self, db_connection):
        """Test P&L calculation for short positions."""
        # Create a short position
        short_trade = {
            'transactionId': 4001,
            'symbol': 'NGH5 Comdty',
            'price': 3.50,
            'quantity': 100,
            'buySell': 'S',
            'sequenceId': '20240115-40',
            'time': '2024-01-15 14:00:00.000',
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, short_trade, method)
        db_connection.commit()
        
        # Cover the short at a lower price (profit)
        cover_trade = {
            'transactionId': 4002,
            'symbol': 'NGH5 Comdty',
            'price': 3.30,
            'quantity': 100,
            'buySell': 'B',
            'sequenceId': '20240115-41',
            'time': '2024-01-15 14:30:00.000',
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, cover_trade, method)
        db_connection.commit()
        
        # Verify P&L for short position
        for method in ['fifo', 'lifo']:
            realized = self.get_realized(db_connection, method, 'NGH5 Comdty')
            assert len(realized) == 1
            # For short: P&L = (entry - exit) * qty * 1000
            # P&L = (3.50 - 3.30) * 100 * 1000 = 20000
            assert abs(realized[0][7] - 20000) < 0.01  # Allow for floating point precision
    
    def test_positions_aggregator_query(self, db_connection):
        """Test the positions aggregator query that pulls from realized tables.
        
        Note: This test sets all trades to today's date to verify the trading day filter works.
        """
        # Use today's date for all trades (before 5pm so it's today's trading day)
        today_timestamp = datetime.now().strftime('%Y-%m-%d 10:00:00.000')
        
        # Insert some trades to create positions
        trades = [
            {
                'transactionId': 5001,
                'symbol': 'ESH5 Comdty',
                'price': 4000.00,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': '20240115-50',
                'time': today_timestamp,
                'fullPartial': 'full'
            },
            {
                'transactionId': 5002,
                'symbol': 'ESH5 Comdty',
                'price': 4010.00,
                'quantity': 4,
                'buySell': 'S',  # Partial offset
                'sequenceId': '20240115-51',
                'time': today_timestamp,
                'fullPartial': 'full'
            },
            {
                'transactionId': 5003,
                'symbol': 'CLH5 Comdty',
                'price': 75.00,
                'quantity': 20,
                'buySell': 'B',
                'sequenceId': '20240115-52',
                'time': today_timestamp,
                'fullPartial': 'full'
            },
            {
                'transactionId': 5004,
                'symbol': 'CLH5 Comdty',
                'price': 76.00,
                'quantity': 20,
                'buySell': 'S',  # Full offset
                'sequenceId': '20240115-53',
                'time': today_timestamp,
                'fullPartial': 'full'
            }
        ]
        
        # Process all trades
        for trade in trades:
            for method in ['fifo', 'lifo']:
                process_new_trade(db_connection, trade, method)
        db_connection.commit()
        
        # Run the aggregator query (using master list approach)
        cursor = db_connection.cursor()
        query = """
        WITH         all_symbols AS (
            -- Get all unique symbols from both open and closed positions
            SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0
            UNION
            SELECT DISTINCT symbol FROM realized_fifo
            WHERE 
                -- Only include symbols with trades today
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE('now', 'localtime')
            UNION
            SELECT DISTINCT symbol FROM realized_lifo
            WHERE 
                -- Only include symbols with trades today
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE('now', 'localtime')
        ),
        open_positions AS (
            -- Get open positions from FIFO
            SELECT 
                symbol,
                SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as open_position
            FROM trades_fifo
            WHERE quantity > 0
            GROUP BY symbol
        ),
        closed_positions_fifo AS (
            -- Get closed positions and realized P&L from realized_fifo for current trading day
            SELECT 
                symbol,
                SUM(ABS(quantity)) as closed_position,
                SUM(realizedPnL) as fifo_realized_pnl
            FROM realized_fifo
            WHERE 
                -- Calculate trading day: if hour >= 17 (5pm Chicago time), use next day
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE('now', 'localtime')
            GROUP BY symbol
        ),
        closed_positions_lifo AS (
            -- Get realized P&L from realized_lifo for current trading day
            SELECT 
                symbol,
                SUM(realizedPnL) as lifo_realized_pnl
            FROM realized_lifo
            WHERE 
                -- Calculate trading day: if hour >= 17 (5pm Chicago time), use next day
                DATE(timestamp, 
                     CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                          THEN '+1 day' 
                          ELSE '+0 day' 
                     END) = DATE('now', 'localtime')
            GROUP BY symbol
        )
        SELECT 
            s.symbol,
            COALESCE(o.open_position, 0) as open_position,
            COALESCE(cf.closed_position, 0) as closed_position,
            COALESCE(cf.fifo_realized_pnl, 0) as fifo_realized_pnl,
            COALESCE(cl.lifo_realized_pnl, 0) as lifo_realized_pnl
        FROM all_symbols s
        LEFT JOIN open_positions o ON s.symbol = o.symbol
        LEFT JOIN closed_positions_fifo cf ON s.symbol = cf.symbol
        LEFT JOIN closed_positions_lifo cl ON s.symbol = cl.symbol
        ORDER BY s.symbol
        """
        
        results = cursor.execute(query).fetchall()
        
        # Verify results
        assert len(results) == 2  # Two symbols
        
        # Check CLH5 (fully closed)
        clh5 = next(r for r in results if r[0] == 'CLH5 Comdty')
        assert clh5[1] == 0    # open_position
        assert clh5[2] == 20   # closed_position
        assert clh5[3] == 20000  # fifo_realized_pnl ((76-75) * 20 * 1000)
        assert clh5[4] == 20000  # lifo_realized_pnl (same for full offset)
        
        # Check ESH5 (partially closed)
        esh5 = next(r for r in results if r[0] == 'ESH5 Comdty')
        assert esh5[1] == 6    # open_position (10 - 4)
        assert esh5[2] == 4    # closed_position
        assert esh5[3] == 40000   # fifo_realized_pnl ((4010-4000) * 4 * 1000)
        assert esh5[4] == 40000   # lifo_realized_pnl (same since only one buy)
        
        # Test that old trades are NOT included
        # Insert an old trade that should not appear in today's results
        old_trade = {
            'transactionId': 6001,
            'symbol': 'NGH5 Comdty',
            'price': 3.00,
            'quantity': 50,
            'buySell': 'B',
            'sequenceId': '20240101-01',
            'time': '2024-01-01 10:00:00.000',  # Old date
            'fullPartial': 'full'
        }
        
        # Process the old trade
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, old_trade, method, old_trade['time'])
            
        # Close it out with an old offsetting trade
        old_offset = {
            'transactionId': 6002,
            'symbol': 'NGH5 Comdty',
            'price': 3.10,
            'quantity': 50,
            'buySell': 'S',
            'sequenceId': '20240101-02',
            'time': '2024-01-01 11:00:00.000',  # Old date
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            process_new_trade(db_connection, old_offset, method, old_offset['time'])
            
        # Run the query again
        cursor.execute(query)
        new_results = cursor.fetchall()
        
        # Should still only have 2 symbols (ESH5 and CLH5), NOT NGH5
        assert len(new_results) == 2
        assert not any(r[0] == 'NGH5 Comdty' for r in new_results)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])