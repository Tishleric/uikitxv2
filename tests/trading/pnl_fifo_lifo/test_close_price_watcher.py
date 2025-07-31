"""
Test close price watcher CSV parsing functionality
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceFileHandler
from lib.trading.pnl_fifo_lifo.config import FUTURES_SYMBOLS


class TestClosePriceWatcher:
    """Test the close price watcher parsing logic"""
    
    @pytest.fixture
    def handler(self):
        """Create a handler instance for testing"""
        return ClosePriceFileHandler(db_path=':memory:', startup_time=0)
    
    def test_process_futures_file_with_settle_prices(self, handler):
        """Test parsing futures CSV when status is Y (use settle prices)"""
        # Create test CSV content matching the reference format
        csv_content = """SYMBOL,PX_SETTLE,PX_300,PX_SETTLE_DEC,PX_300_DEC,Settle Price = Today
TU,103-20 7/8,,103.65234375,#N/A N/A,Y
FV,108-14 1/4,,108.4453125,#N/A N/A,Y
TY,111-11 1/2,,111.359375,#N/A N/A,Y
US,114-17,,114.53125,#N/A N/A,Y
RX,129-65,,129.66,,"""
        
        # Use a temporary directory to avoid file locking issues on Windows
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_futures_file(temp_file)
            
            # Verify correct symbols and prices were extracted
            assert len(prices) == 5
            assert prices['TUU5 Comdty'] == 103.65234375
            assert prices['FVU5 Comdty'] == 108.4453125
            assert prices['TYU5 Comdty'] == 111.359375
            assert prices['USU5 Comdty'] == 114.53125
            assert prices['RXU5 Comdty'] == 129.66
    
    def test_process_futures_file_with_flash_prices(self, handler):
        """Test parsing futures CSV when status is not Y (use flash prices)"""
        csv_content = """SYMBOL,PX_SETTLE,PX_300,PX_SETTLE_DEC,PX_300_DEC,Settle Price = Today
TU,103-20 7/8,,103.65234375,103.50,N
FV,108-14 1/4,,108.4453125,108.40,N
TY,111-11 1/2,,111.359375,111.25,N"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_futures_file(temp_file)
            
            # Should use flash prices (PX_300_DEC) when status is N
            assert len(prices) == 3
            assert prices['TUU5 Comdty'] == 103.50
            assert prices['FVU5 Comdty'] == 108.40
            assert prices['TYU5 Comdty'] == 111.25
    
    def test_process_options_file_with_settle_prices(self, handler):
        """Test parsing options CSV when status is Y (use settle prices)"""
        csv_content = """SYMBOL,LAST_PRICE,PX_SETTLE,Expiry Date,Settle Price = Today
TJPN25P5 114.25 Comdty,-2146826238,2.890625,2025-07-29,Y
TJPN25P5 114 Comdty,-2146826238,2.640625,2025-07-29,Y
TJPN25P5 113.75 Comdty,-2146826238,2.390625,2025-07-29,Y
TYWN25P5 114.25 COMB Comdty,-2146826238,3.484375,2025-07-30,N
TYWN25P5 114 COMB Comdty,-2146826238,3.234375,2025-07-30,N"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_options_file(temp_file)
            
            # Should use settle prices for Y status, flash (LAST_PRICE) for N
            assert len(prices) == 3  # Only 3 with valid prices
            # Y status - use PX_SETTLE
            assert prices['TJPN25P5 114.25 Comdty'] == 2.890625
            assert prices['TJPN25P5 114 Comdty'] == 2.640625
            assert prices['TJPN25P5 113.75 Comdty'] == 2.390625
            # N status - would use LAST_PRICE but it's invalid (-2146826238)
            # so these should be skipped
            assert 'TYWN25P5 114.25 COMB Comdty' not in prices
            assert 'TYWN25P5 114 COMB Comdty' not in prices
    
    def test_process_options_file_with_flash_prices(self, handler):
        """Test parsing options CSV when status is N (use flash prices)"""
        csv_content = """SYMBOL,LAST_PRICE,PX_SETTLE,Expiry Date,Settle Price = Today
TYWN25P5 114.25 COMB Comdty,0.0156,3.484375,2025-07-30,N
TYWN25P5 114 COMB Comdty,0.0312,3.234375,2025-07-30,N
TYWN25C5 114.25 COMB Comdty,0.0625,0.0010000001639127731,2025-07-30,N"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_options_file(temp_file)
            
            # Should use LAST_PRICE when status is N
            # Symbols should have 'COMB' removed
            assert len(prices) == 3
            assert prices['TYWN25P5 114.25 Comdty'] == 0.0156
            assert prices['TYWN25P5 114 Comdty'] == 0.0312
            assert prices['TYWN25C5 114.25 Comdty'] == 0.0625
    
    def test_skip_invalid_rows(self, handler):
        """Test that invalid rows are skipped properly"""
        csv_content = """SYMBOL,LAST_PRICE,PX_SETTLE,Expiry Date,Settle Price = Today
TJPN25P5 114.25 Comdty,0.15,2.890625,2025-07-29,Y
0.0,-2146826238,#N/A Mandatory parameter [SECURITY] cannot be empty,1899-12-30,
,0.25,0.50,2025-07-30,N
VALID_SYMBOL Comdty,0.30,0.60,2025-07-30,N"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_options_file(temp_file)
            
            # Should only process valid rows
            assert len(prices) == 2
            assert prices['TJPN25P5 114.25 Comdty'] == 2.890625  # Y status
            assert prices['VALID_SYMBOL Comdty'] == 0.30  # N status
    
    def test_comb_removal(self, handler):
        """Test that COMB is properly removed from option symbols"""
        csv_content = """SYMBOL,LAST_PRICE,PX_SETTLE,Expiry Date,Settle Price = Today
TYWN25P5 114.25 COMB Comdty,0.0156,3.484375,2025-07-30,N
TJPN25P5 114.25 Comdty,0.15,2.890625,2025-07-29,Y
1MQ5C 110.5 COMB Comdty,0.25,0.484375,2025-08-01,N
VBYQ25C1 110 Comdty,0.30,0.859375,2025-08-04,Y"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_options_file(temp_file)
            
            # Check that COMB was removed from symbols that had it
            assert 'TYWN25P5 114.25 Comdty' in prices  # Had COMB, should be removed
            assert 'TJPN25P5 114.25 Comdty' in prices  # No COMB, unchanged
            assert '1MQ5C 110.5 Comdty' in prices      # Had COMB, should be removed
            assert 'VBYQ25C1 110 Comdty' in prices     # No COMB, unchanged
            
            # Verify no symbols with COMB remain
            for symbol in prices.keys():
                assert ' COMB ' not in symbol
    
    def test_handle_missing_columns(self, handler):
        """Test graceful handling of missing columns"""
        # Futures file missing required column
        csv_content = """SYMBOL,PX_SETTLE,PX_300
TU,103-20 7/8,
FV,108-14 1/4,"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / 'test.csv'
            temp_file.write_text(csv_content)
            
            prices = handler._process_futures_file(temp_file)
            # Should return empty dict due to missing columns
            assert prices == {}