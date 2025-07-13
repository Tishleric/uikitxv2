"""Unit tests for P&L Calculator module.

Tests cover FIFO logic, realized/unrealized P&L calculations,
and various edge cases including short positions.
"""

import pytest
from datetime import datetime, date
import pandas as pd

from lib.trading.pnl_calculator import PnLCalculator, Trade, Lot


class TestModels:
    """Test the Trade and Lot data models."""
    
    def test_trade_validation(self):
        """Test Trade model validation."""
        # Valid trade
        trade = Trade(
            timestamp=datetime(2024, 1, 1, 9, 30),
            symbol="AAPL",
            quantity=10,
            price=100.0
        )
        assert trade.quantity == 10
        assert trade.price == 100.0
        
        # Invalid trades
        with pytest.raises(ValueError, match="quantity cannot be zero"):
            Trade(datetime.now(), "AAPL", 0, 100.0)
            
        with pytest.raises(ValueError, match="price cannot be negative"):
            Trade(datetime.now(), "AAPL", 10, -100.0)
            
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            Trade(datetime.now(), "", 10, 100.0)
    
    def test_lot_validation(self):
        """Test Lot model validation."""
        # Valid lot
        lot = Lot(quantity=10, price=100.0, date=date.today())
        assert lot.quantity == 10
        
        # Invalid lots
        with pytest.raises(ValueError, match="quantity cannot be zero"):
            Lot(0, 100.0, date.today())
            
        with pytest.raises(ValueError, match="price cannot be negative"):
            Lot(10, -100.0, date.today())


class TestPnLCalculator:
    """Test the main P&L Calculator functionality."""
    
    def test_simple_buy_sell(self):
        """Test simple buy and sell with profit."""
        calc = PnLCalculator()
        
        # Add trades
        calc.add_trade(datetime(2024, 1, 1), "AAPL", 10, 100.0)  # Buy 10 @ 100
        calc.add_trade(datetime(2024, 1, 2), "AAPL", -10, 110.0)  # Sell 10 @ 110
        
        # Add market closes
        calc.add_market_close("AAPL", date(2024, 1, 1), 100.0)
        calc.add_market_close("AAPL", date(2024, 1, 2), 110.0)
        
        # Calculate P&L
        df = calc.calculate_daily_pnl()
        
        # Check results
        assert len(df) == 2
        
        # Day 1: Just bought, no realized P&L
        day1 = df[df['date'] == date(2024, 1, 1)].iloc[0]
        assert day1['realized_pnl'] == 0
        assert day1['position'] == 10
        
        # Day 2: Sold all, realized profit of 100
        day2 = df[df['date'] == date(2024, 1, 2)].iloc[0]
        assert day2['realized_pnl'] == 100.0  # (110-100) * 10
        assert day2['position'] == 0
        assert day2['unrealized_pnl'] == 0
        
    def test_partial_sell(self):
        """Test partial sell of position."""
        calc = PnLCalculator()
        
        # Buy 10, sell 5
        calc.add_trade(datetime(2024, 1, 1), "AAPL", 10, 100.0)
        calc.add_trade(datetime(2024, 1, 2), "AAPL", -5, 110.0)
        
        calc.add_market_close("AAPL", date(2024, 1, 1), 100.0)
        calc.add_market_close("AAPL", date(2024, 1, 2), 110.0)
        
        df = calc.calculate_daily_pnl()
        
        # Day 2: Sold 5, realized profit of 50, still have 5 left
        day2 = df[df['date'] == date(2024, 1, 2)].iloc[0]
        assert day2['realized_pnl'] == 50.0  # (110-100) * 5
        assert day2['position'] == 5
        assert day2['unrealized_pnl'] == 50.0  # (110-100) * 5 remaining
        
    def test_short_position(self):
        """Test short selling and covering."""
        calc = PnLCalculator()
        
        # Short sell 10 @ 100
        calc.add_trade(datetime(2024, 1, 1), "AAPL", -10, 100.0)
        # Cover short @ 90 (profit)
        calc.add_trade(datetime(2024, 1, 2), "AAPL", 10, 90.0)
        
        calc.add_market_close("AAPL", date(2024, 1, 1), 100.0)
        calc.add_market_close("AAPL", date(2024, 1, 2), 90.0)
        
        df = calc.calculate_daily_pnl()
        
        # Day 1: Short position
        day1 = df[df['date'] == date(2024, 1, 1)].iloc[0]
        assert day1['position'] == -10
        assert day1['unrealized_pnl'] == 0  # No change from entry price
        
        # Day 2: Covered short with profit
        day2 = df[df['date'] == date(2024, 1, 2)].iloc[0]
        assert day2['realized_pnl'] == 100.0  # (100-90) * 10
        assert day2['position'] == 0
        
    def test_fifo_ordering(self):
        """Test FIFO ordering of lots."""
        calc = PnLCalculator()
        
        # Buy at different prices
        calc.add_trade(datetime(2024, 1, 1, 9, 0), "AAPL", 5, 100.0)
        calc.add_trade(datetime(2024, 1, 1, 10, 0), "AAPL", 5, 105.0)
        
        # Sell 5 - should sell from first lot (FIFO)
        calc.add_trade(datetime(2024, 1, 2), "AAPL", -5, 110.0)
        
        calc.add_market_close("AAPL", date(2024, 1, 1), 102.0)
        calc.add_market_close("AAPL", date(2024, 1, 2), 110.0)
        
        df = calc.calculate_daily_pnl()
        
        # Day 2: Should have sold the 100 lot, not the 105 lot
        day2 = df[df['date'] == date(2024, 1, 2)].iloc[0]
        assert day2['realized_pnl'] == 50.0  # (110-100) * 5
        assert day2['avg_cost'] == 105.0  # Only 105 lot remains
        
    def test_position_summary(self):
        """Test position summary functionality."""
        calc = PnLCalculator()
        
        # Multiple symbols
        calc.add_trade(datetime(2024, 1, 1), "AAPL", 10, 100.0)
        calc.add_trade(datetime(2024, 1, 1), "MSFT", 20, 200.0)
        calc.add_trade(datetime(2024, 1, 2), "AAPL", -5, 110.0)
        
        calc.add_market_close("AAPL", date(2024, 1, 2), 110.0)
        calc.add_market_close("MSFT", date(2024, 1, 2), 210.0)
        
        # Get position summary
        summary = calc.get_position_summary(as_of_date=date(2024, 1, 2))
        
        assert len(summary) == 2
        
        # Check AAPL position
        aapl_pos = summary[summary['symbol'] == 'AAPL'].iloc[0]
        assert aapl_pos['position'] == 5
        assert aapl_pos['avg_cost'] == 100.0
        assert aapl_pos['unrealized_pnl'] == 50.0
        
        # Check MSFT position
        msft_pos = summary[summary['symbol'] == 'MSFT'].iloc[0]
        assert msft_pos['position'] == 20
        assert msft_pos['avg_cost'] == 200.0
        assert msft_pos['unrealized_pnl'] == 200.0
        
    def test_invalid_market_close(self):
        """Test invalid market close price."""
        calc = PnLCalculator()
        
        with pytest.raises(ValueError, match="Market close price cannot be negative"):
            calc.add_market_close("AAPL", date.today(), -100.0)
            
    def test_empty_calculator(self):
        """Test calculator with no trades."""
        calc = PnLCalculator()
        
        # Should return empty DataFrame
        df = calc.calculate_daily_pnl()
        assert df.empty
        
        # Position summary should also be empty
        summary = calc.get_position_summary()
        assert summary.empty 