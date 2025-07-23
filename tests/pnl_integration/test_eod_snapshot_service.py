"""
Tests for EOD P&L Snapshot Service - Phase 1

Tests focus on:
1. Table creation and schema validation
2. Settlement boundary calculations
3. Timezone handling (CDT)
4. TOTAL row aggregation
5. EOD snapshot data structure
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, date, time
import pytz

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.pnl_integration.settlement_constants import (
    CHICAGO_TZ, SETTLEMENT_TIME, EOD_TIME,
    get_settlement_boundaries, get_eod_boundary,
    is_before_settlement, split_position_at_settlement
)


class TestSettlementConstants:
    """Test settlement time calculations and utilities."""
    
    def test_chicago_timezone(self):
        """Test Chicago timezone is correctly configured."""
        assert CHICAGO_TZ.zone == 'America/Chicago'
        
        # Test DST handling
        summer_date = datetime(2025, 7, 15, 14, 0)  # July - CDT
        winter_date = datetime(2025, 1, 15, 14, 0)  # January - CST
        
        summer_ct = CHICAGO_TZ.localize(summer_date)
        winter_ct = CHICAGO_TZ.localize(winter_date)
        
        # In summer, Chicago is UTC-5, in winter UTC-6
        assert summer_ct.strftime('%z') == '-0500'
        assert winter_ct.strftime('%z') == '-0600'
    
    def test_settlement_boundaries(self):
        """Test calculation of settlement boundaries."""
        trade_date = date(2025, 7, 22)
        prev_4pm, curr_2pm = get_settlement_boundaries(trade_date)
        
        # Previous day 4pm
        assert prev_4pm.date() == date(2025, 7, 21)
        assert prev_4pm.time() == EOD_TIME
        assert prev_4pm.tzinfo == CHICAGO_TZ
        
        # Current day 2pm
        assert curr_2pm.date() == trade_date
        assert curr_2pm.time() == SETTLEMENT_TIME
        assert curr_2pm.tzinfo == CHICAGO_TZ
    
    def test_eod_boundary(self):
        """Test EOD boundary calculation."""
        trade_date = date(2025, 7, 22)
        eod = get_eod_boundary(trade_date)
        
        assert eod.date() == trade_date
        assert eod.time() == EOD_TIME
        assert eod.tzinfo == CHICAGO_TZ
    
    def test_is_before_settlement(self):
        """Test settlement time comparison."""
        trade_date = date(2025, 7, 22)
        
        # 11am - before settlement
        morning_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(11, 0))
        )
        assert is_before_settlement(morning_time, trade_date) is True
        
        # 3pm - after settlement
        afternoon_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(15, 0))
        )
        assert is_before_settlement(afternoon_time, trade_date) is False
        
        # Exactly 2pm - not before
        settlement_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(14, 0))
        )
        assert is_before_settlement(settlement_time, trade_date) is False
    
    def test_split_position_at_settlement(self):
        """Test position splitting at settlement boundary."""
        trade_date = date(2025, 7, 22)
        
        # Position from 11am to 3pm (crosses settlement)
        entry_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(11, 0))
        )
        exit_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(15, 0))
        )
        
        segments = split_position_at_settlement(entry_time, exit_time, trade_date)
        
        assert len(segments) == 2
        
        # First segment: 11am to 2pm
        seg1_start, seg1_end, seg1_type = segments[0]
        assert seg1_start == entry_time
        assert seg1_end.time() == SETTLEMENT_TIME
        assert seg1_type == 'pre_settlement'
        
        # Second segment: 2pm to 3pm
        seg2_start, seg2_end, seg2_type = segments[1]
        assert seg2_start.time() == SETTLEMENT_TIME
        assert seg2_end == exit_time
        assert seg2_type == 'post_settlement'
    
    def test_split_position_no_crossing(self):
        """Test position that doesn't cross settlement."""
        trade_date = date(2025, 7, 22)
        
        # Morning only position (9am to 11am)
        entry_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(9, 0))
        )
        exit_time = CHICAGO_TZ.localize(
            datetime.combine(trade_date, time(11, 0))
        )
        
        segments = split_position_at_settlement(entry_time, exit_time, trade_date)
        
        assert len(segments) == 1
        assert segments[0][2] == 'pre_settlement'


class TestEODHistoryTable:
    """Test EOD history table creation and structure."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
            db_path = tf.name
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_table_creation(self, temp_db):
        """Test that migration creates correct table structure."""
        # Import and run migration
        from scripts.migration import add_eod_history_table_002 as migration
        
        migration.migrate_up(temp_db)
        
        # Check table exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tyu5_eod_pnl_history'
        """)
        
        assert cursor.fetchone() is not None
        
        # Check columns
        cursor.execute("PRAGMA table_info(tyu5_eod_pnl_history)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        expected_columns = {
            'id': 'INTEGER',
            'snapshot_date': 'DATE',
            'symbol': 'TEXT',
            'position_quantity': 'REAL',
            'realized_pnl': 'REAL',
            'unrealized_pnl_settle': 'REAL',
            'unrealized_pnl_current': 'REAL',
            'total_daily_pnl': 'REAL',
            'settlement_price': 'REAL',
            'current_price': 'REAL',
            'created_at': 'TIMESTAMP'
        }
        
        for col, dtype in expected_columns.items():
            assert col in columns
            assert columns[col] == dtype
        
        conn.close()
    
    def test_unique_constraint(self, temp_db):
        """Test unique constraint on (snapshot_date, symbol)."""
        from scripts.migration import add_eod_history_table_002 as migration
        
        migration.migrate_up(temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert a record
        cursor.execute("""
            INSERT INTO tyu5_eod_pnl_history
            (snapshot_date, symbol, position_quantity, realized_pnl,
             unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl)
            VALUES ('2025-07-22', 'TYU5 Comdty', 10, 100, 200, 250, 350)
        """)
        
        # Try to insert duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO tyu5_eod_pnl_history
                (snapshot_date, symbol, position_quantity, realized_pnl,
                 unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl)
                VALUES ('2025-07-22', 'TYU5 Comdty', 20, 200, 300, 350, 550)
            """)
        
        conn.close()
    
    def test_views_creation(self, temp_db):
        """Test that views are created correctly."""
        from scripts.migration import add_eod_history_table_002 as migration
        
        migration.migrate_up(temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check views exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' 
            ORDER BY name
        """)
        
        views = [row[0] for row in cursor.fetchall()]
        assert 'tyu5_daily_pnl_totals' in views
        assert 'tyu5_latest_eod_snapshot' in views
        
        conn.close()
    
    def test_total_row_aggregation(self, temp_db):
        """Test TOTAL row aggregation logic."""
        from scripts.migration import add_eod_history_table_002 as migration
        
        migration.migrate_up(temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert test data
        test_data = [
            ('2025-07-22', 'TYU5 Comdty', 10, 100, 200, 250, 350),
            ('2025-07-22', 'ZNU5 Comdty', -5, 50, -100, -80, -30),
            ('2025-07-22', 'TOTAL', 0, 150, 100, 170, 320)
        ]
        
        for row in test_data:
            cursor.execute("""
                INSERT INTO tyu5_eod_pnl_history
                (snapshot_date, symbol, position_quantity, realized_pnl,
                 unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row)
        
        # Query aggregated view (should exclude TOTAL row)
        cursor.execute("""
            SELECT * FROM tyu5_daily_pnl_totals
            WHERE snapshot_date = '2025-07-22'
        """)
        
        result = cursor.fetchone()
        assert result is not None
        
        # Check aggregation matches manual TOTAL
        _, symbol_count, _, _, total_realized, total_unrealized_settle, total_unrealized_current, total_pnl = result
        
        assert symbol_count == 2  # Excludes TOTAL row
        assert total_realized == 150
        assert total_unrealized_settle == 100
        assert total_unrealized_current == 170
        assert total_pnl == 320
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 