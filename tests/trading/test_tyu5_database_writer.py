#!/usr/bin/env python
"""Test TYU5 Database Writer

This test suite ensures the TYU5DatabaseWriter correctly persists calculation
results to the database tables created in Phase 1.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter
from lib.trading.pnl_calculator.storage import PnLStorage


class TestTYU5DatabaseWriter:
    """Test suite for TYU5 database writer."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with schema."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize schema
        storage = PnLStorage(path)
        
        yield path
        os.unlink(path)
        
    @pytest.fixture
    def sample_data(self):
        """Create sample TYU5 output data."""
        # Positions DataFrame
        positions_df = pd.DataFrame({
            'Symbol': ['TYU5', 'VBYN25C2', 'VBYN25P3'],
            'Type': ['FUT', 'CALL', 'PUT'],
            'Net_Quantity': [10, -5, 3],
            'Avg_Entry_Price': [120.5, 2.25, 1.75],
            'Current_Price': [121.0, 2.50, 1.60],
            'Unrealized_PnL': [500, -125, -45],
            'Daily_PnL': [200, -50, -30],
            'Total_PnL': [500, -125, -45]
        })
        
        # Trades DataFrame
        trades_df = pd.DataFrame({
            'Symbol': ['TYU5', 'TYU5', 'VBYN25C2'],
            'DateTime': ['2025-01-15 09:00:00', '2025-01-15 10:00:00', '2025-01-15 11:00:00'],
            'Action': ['BUY', 'BUY', 'SELL'],
            'Quantity': [5, 5, 5],
            'Price': [120.0, 121.0, 2.25],
            'Realized_PnL': [0, 0, 0],
            'trade_id': ['T001', 'T002', 'T003']
        })
        
        # Position Breakdown DataFrame
        breakdown_df = pd.DataFrame({
            'Symbol': ['TYU5', 'TYU5', 'VBYN25C2'],
            'Trade_ID': ['T001', 'T002', 'T003'],
            'Entry_Date': ['2025-01-15 09:00:00', '2025-01-15 10:00:00', '2025-01-15 11:00:00'],
            'Entry_Price': [120.0, 121.0, 2.25],
            'Remaining_Qty': [5, 5, 5],
            'Current_Price': [121.0, 121.0, 2.50]
        })
        
        # Risk Matrix DataFrame
        risk_df = pd.DataFrame({
            'Price': [118.0, 119.0, 120.0, 121.0, 122.0, 123.0, 124.0],
            'Price_Change': [-3, -2, -1, 0, 1, 2, 3],
            'TYU5_PnL': [-3000, -2000, -1000, 0, 1000, 2000, 3000],
            'VBYN25C2_PnL': [375, 250, 125, 0, -125, -250, -375],
            'VBYN25P3_PnL': [-225, -150, -75, 0, 75, 150, 225],
            'Total_PnL': [-2850, -1900, -950, 0, 950, 1900, 2850]
        })
        
        return {
            'positions': positions_df,
            'trades': trades_df,
            'breakdown': breakdown_df,
            'risk': risk_df
        }
        
    def test_write_lot_positions(self, temp_db, sample_data):
        """Test writing lot positions to database."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # Write results
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=sample_data['trades'],
            breakdown_df=sample_data['breakdown'],
            calc_timestamp=calc_timestamp
        )
        
        assert success, "Write operation should succeed"
        
        # Verify lot positions were written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM lot_positions")
            count = cursor.fetchone()[0]
            assert count == 3, f"Expected 3 lot positions, got {count}"
            
            # Verify specific lot
            cursor.execute("""
                SELECT symbol, trade_id, remaining_quantity, entry_price 
                FROM lot_positions 
                WHERE trade_id = 'T001'
            """)
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 'TYU5'
            assert row[2] == 5  # remaining_quantity
            assert row[3] == 120.0  # entry_price
            
    def test_write_position_greeks(self, temp_db, sample_data):
        """Test writing Greek values for options."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # First create positions in positions table
        with sqlite3.connect(temp_db) as conn:
            conn.executemany("""
                INSERT INTO positions (instrument_name, position_quantity, avg_cost,
                                     total_realized_pnl, unrealized_pnl, last_updated, is_option)
                VALUES (?, ?, ?, 0, ?, ?, ?)
            """, [
                ('VBYN25C2', -5, 2.25, -125, calc_timestamp, 1),
                ('VBYN25P3', 3, 1.75, -45, calc_timestamp, 1)
            ])
            conn.commit()
            
        # Write results
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=sample_data['trades'],
            breakdown_df=sample_data['breakdown'],
            calc_timestamp=calc_timestamp
        )
        
        assert success
        
        # Verify Greeks were written for options
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM position_greeks")
            count = cursor.fetchone()[0]
            assert count >= 2, f"Expected at least 2 Greek records, got {count}"
            
    def test_write_risk_scenarios(self, temp_db, sample_data):
        """Test writing risk scenario matrix."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # Write results with risk matrix
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=sample_data['trades'],
            breakdown_df=sample_data['breakdown'],
            risk_df=sample_data['risk'],
            calc_timestamp=calc_timestamp
        )
        
        assert success
        
        # Verify risk scenarios were written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM risk_scenarios")
            count = cursor.fetchone()[0]
            # 3 symbols × 7 scenarios = 21 records
            assert count == 21, f"Expected 21 risk scenarios, got {count}"
            
            # Verify specific scenario
            cursor.execute("""
                SELECT scenario_price, scenario_pnl, position_quantity
                FROM risk_scenarios
                WHERE symbol = 'TYU5' AND scenario_price = 122.0
            """)
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == 1000  # scenario_pnl
            assert row[2] == 10  # position_quantity
            
    def test_write_match_history(self, temp_db, sample_data):
        """Test writing FIFO match history."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # Add realized P&L to trades
        trades_with_pnl = sample_data['trades'].copy()
        trades_with_pnl.loc[2, 'Realized_PnL'] = 125  # Sell trade has realized P&L
        
        # Write results
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=trades_with_pnl,
            breakdown_df=sample_data['breakdown'],
            calc_timestamp=calc_timestamp
        )
        
        assert success
        
        # Verify match history
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM match_history")
            count = cursor.fetchone()[0]
            assert count >= 1, f"Expected at least 1 match record, got {count}"
            
    def test_update_positions_table(self, temp_db, sample_data):
        """Test updating positions table with short quantities."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # Create positions
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                INSERT INTO positions (instrument_name, position_quantity, avg_cost,
                                     total_realized_pnl, unrealized_pnl, last_updated)
                VALUES ('VBYN25C2', -5, 2.25, 0, -125, ?)
            """, (calc_timestamp,))
            conn.commit()
            
        # Write results
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=sample_data['trades'],
            breakdown_df=sample_data['breakdown'],
            calc_timestamp=calc_timestamp
        )
        
        assert success
        
        # Verify short_quantity was updated
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT short_quantity FROM positions WHERE instrument_name = 'VBYN25C2'
            """)
            short_qty = cursor.fetchone()[0]
            assert short_qty == 5, f"Expected short_quantity of 5, got {short_qty}"
            
    def test_vtexp_loading(self, temp_db):
        """Test loading latest vtexp file."""
        writer = TYU5DatabaseWriter(temp_db)
        
        # Load vtexp (if directory exists)
        vtexp_map = writer._load_latest_vtexp()
        
        # If vtexp files exist, verify structure
        if vtexp_map:
            assert isinstance(vtexp_map, dict)
            # Check for expected format
            for symbol, vtexp in vtexp_map.items():
                assert isinstance(symbol, str)
                assert isinstance(vtexp, (int, float))
                
    def test_transaction_rollback(self, temp_db, sample_data):
        """Test that failed writes rollback properly."""
        writer = TYU5DatabaseWriter(temp_db)
        calc_timestamp = datetime.now()
        
        # Create invalid data that will cause failure
        bad_breakdown = sample_data['breakdown'].copy()
        bad_breakdown['Remaining_Qty'] = 'invalid'  # Non-numeric value
        
        # Write should fail
        success = writer.write_results(
            positions_df=sample_data['positions'],
            trades_df=sample_data['trades'],
            breakdown_df=bad_breakdown,
            calc_timestamp=calc_timestamp
        )
        
        assert not success, "Write should fail with invalid data"
        
        # Verify no partial data was written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM lot_positions")
            count = cursor.fetchone()[0]
            assert count == 0, "No data should be written on failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 