#!/usr/bin/env python
"""Test Enhanced Unified Service with TYU5 Features

This test suite verifies the unified service correctly integrates
TradePreprocessor data with TYU5 advanced features.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_integration.unified_pnl_api import UnifiedPnLAPI


class TestUnifiedServiceEnhanced:
    """Test suite for enhanced unified service."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with test data."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize schema
        storage = PnLStorage(path)
        
        # Add test data
        conn = sqlite3.connect(path)
        
        # Add positions
        conn.executemany("""
            INSERT INTO positions (instrument_name, position_quantity, avg_cost,
                                 total_realized_pnl, unrealized_pnl, last_updated, 
                                 is_option, short_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('TYU5 Comdty', 100, 120.5, 1000, -500, datetime.now(), 0, 0),
            ('VBYN25C2 Comdty', -50, 2.25, 500, -125, datetime.now(), 1, 50),
            ('VBYN25P3 Comdty', 30, 1.75, 0, -45, datetime.now(), 1, 0)
        ])
        
        # Add lot positions
        conn.executemany("""
            INSERT INTO lot_positions (symbol, trade_id, remaining_quantity, 
                                     entry_price, entry_date)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ('TYU5 Comdty', 'T001', 60, 120.0, datetime.now()),
            ('TYU5 Comdty', 'T002', 40, 121.25, datetime.now()),
            ('VBYN25C2 Comdty', 'T003', -50, 2.25, datetime.now()),
            ('VBYN25P3 Comdty', 'T004', 30, 1.75, datetime.now())
        ])
        
        # Add Greeks for options
        position_ids = []
        cursor = conn.cursor()
        for symbol in ['VBYN25C2 Comdty', 'VBYN25P3 Comdty']:
            cursor.execute("SELECT id FROM positions WHERE instrument_name = ?", (symbol,))
            position_ids.append(cursor.fetchone()[0])
            
        conn.executemany("""
            INSERT INTO position_greeks (position_id, calc_timestamp, underlying_price,
                                       implied_vol, delta, gamma, vega, theta, speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (position_ids[0], datetime.now(), 121.0, 0.15, 0.45, 0.02, 0.3, -0.05, 0.001),
            (position_ids[1], datetime.now(), 121.0, 0.15, -0.35, 0.02, 0.3, -0.04, 0.001)
        ])
        
        # Add risk scenarios
        conn.executemany("""
            INSERT INTO risk_scenarios (calc_timestamp, symbol, scenario_price,
                                      scenario_pnl, position_quantity)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (datetime.now(), 'TYU5 Comdty', 119.0, -200000, 100),
            (datetime.now(), 'TYU5 Comdty', 120.0, -100000, 100),
            (datetime.now(), 'TYU5 Comdty', 121.0, 0, 100),
            (datetime.now(), 'TYU5 Comdty', 122.0, 100000, 100),
            (datetime.now(), 'TYU5 Comdty', 123.0, 200000, 100)
        ])
        
        conn.commit()
        conn.close()
        
        yield path
        os.unlink(path)
        
    def test_unified_service_initialization(self, temp_db):
        """Test unified service initializes with TYU5 features."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        assert service._tyu5_enabled
        assert service.unified_api is not None
        
    def test_get_positions_with_lots(self, temp_db):
        """Test getting positions with lot details."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        positions = service.get_positions_with_lots()
        
        assert len(positions) == 3
        
        # Check TYU5 position has lots
        tyu5_pos = next(p for p in positions if p['symbol'] == 'TYU5 Comdty')
        assert tyu5_pos['lot_count'] == 2
        assert len(tyu5_pos['lots']) == 2
        assert tyu5_pos['lots'][0]['remaining_quantity'] == 60
        assert tyu5_pos['lots'][1]['remaining_quantity'] == 40
        
    def test_get_portfolio_greeks(self, temp_db):
        """Test getting portfolio-level Greeks."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        greeks = service.get_portfolio_greeks()
        
        assert 'total_delta' in greeks
        assert 'total_gamma' in greeks
        assert 'total_vega' in greeks
        assert 'total_theta' in greeks
        assert 'option_count' in greeks
        
        # Check calculations
        # VBYN25C2: -50 * 0.45 = -22.5
        # VBYN25P3: 30 * -0.35 = -10.5
        # Total: -33.0
        assert abs(greeks['total_delta'] - (-33.0)) < 0.01
        
    def test_get_greek_exposure(self, temp_db):
        """Test getting Greek exposure by position."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        exposure = service.get_greek_exposure()
        
        assert len(exposure) == 2  # Two options
        
        # Check individual Greeks
        vbyn25c2 = next(e for e in exposure if e['symbol'] == 'VBYN25C2 Comdty')
        assert vbyn25c2['delta'] == 0.45
        assert vbyn25c2['position_quantity'] == -50
        assert vbyn25c2['position_delta'] == -22.5
        
    def test_get_risk_scenarios(self, temp_db):
        """Test getting risk scenarios."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        scenarios = service.get_risk_scenarios('TYU5 Comdty')
        
        assert len(scenarios) == 5
        assert scenarios[0]['scenario_price'] == 119.0
        assert scenarios[0]['scenario_pnl'] == -200000
        assert scenarios[2]['scenario_price'] == 121.0
        assert scenarios[2]['scenario_pnl'] == 0
        
    def test_get_comprehensive_position_view(self, temp_db):
        """Test getting comprehensive position view."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        position = service.get_comprehensive_position_view('TYU5 Comdty')
        
        assert position is not None
        assert position['symbol'] == 'TYU5 Comdty'
        assert position['net_position'] == 100
        assert len(position['lots']) == 2
        assert len(position['risk_scenarios']) == 5
        
    def test_get_portfolio_summary_enhanced(self, temp_db):
        """Test getting enhanced portfolio summary."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        summary = service.get_portfolio_summary_enhanced()
        
        assert 'positions' in summary
        assert 'lots' in summary
        assert 'greeks' in summary
        assert 'scenarios' in summary
        assert 'basic' in summary
        
        # Check aggregates
        assert summary['positions']['position_count'] == 3
        assert summary['lots']['total_lots'] == 4
        assert summary['greeks']['option_count'] == 2
        
    def test_fallback_without_tyu5(self, temp_db):
        """Test service works without TYU5 features."""
        service = UnifiedPnLService(
            db_path=temp_db,
            trade_ledger_dir="test_trades",
            price_directories=["test_prices"]
        )
        
        # Simulate TYU5 not available
        service._tyu5_enabled = False
        service.unified_api = None
        
        # Should still return basic data
        positions = service.get_positions_with_lots()
        assert len(positions) > 0
        
        greeks = service.get_portfolio_greeks()
        assert greeks['total_delta'] == 0.0
        assert greeks['option_count'] == 0
        
        scenarios = service.get_risk_scenarios()
        assert scenarios == []


class TestUnifiedPnLAPI:
    """Test the UnifiedPnLAPI directly."""
    
    def test_api_queries(self, temp_db):
        """Test API query methods work correctly."""
        api = UnifiedPnLAPI(temp_db)
        
        # Test positions with lots
        positions = api.get_positions_with_lots()
        assert len(positions) == 3
        
        # Test Greek exposure
        greeks_df = api.get_greek_exposure()
        assert len(greeks_df) == 2
        assert 'position_delta' in greeks_df.columns
        
        # Test portfolio Greeks
        portfolio_greeks = api.get_portfolio_greeks()
        assert isinstance(portfolio_greeks['total_delta'], float)
        
        # Test risk scenarios
        scenarios_df = api.get_risk_scenarios()
        assert len(scenarios_df) == 5
        
        # Test comprehensive view
        position = api.get_comprehensive_position_view('TYU5 Comdty')
        assert position is not None
        assert 'lots' in position
        assert 'risk_scenarios' in position


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 