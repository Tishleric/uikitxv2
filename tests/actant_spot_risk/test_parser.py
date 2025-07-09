"""Tests for Actant spot risk parser module."""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
import os

from lib.trading.actant.spot_risk.parser import (
    extract_datetime_from_filename,
    parse_expiry_from_key,
    parse_spot_risk_csv
)


class TestExtractDatetimeFromFilename:
    """Test datetime extraction from filename."""
    
    def test_valid_filename(self):
        """Test parsing valid filename."""
        filename = "bav_analysis_20250708_104022.csv"
        dt = extract_datetime_from_filename(filename)
        assert dt == datetime(2025, 7, 8, 10, 40, 22)
        
    def test_valid_filename_with_path(self):
        """Test parsing filename with full path."""
        filename = "/data/input/actant_spot_risk/bav_analysis_20250708_104022.csv"
        dt = extract_datetime_from_filename(filename)
        assert dt == datetime(2025, 7, 8, 10, 40, 22)
        
    def test_valid_filename_path_object(self):
        """Test parsing Path object."""
        filename = Path("bav_analysis_20250708_104022.csv")
        dt = extract_datetime_from_filename(filename)
        assert dt == datetime(2025, 7, 8, 10, 40, 22)
        
    def test_invalid_filename_format(self):
        """Test invalid filename format raises ValueError."""
        with pytest.raises(ValueError):
            extract_datetime_from_filename("invalid_filename.csv")
            
    def test_invalid_date_format(self):
        """Test invalid date in filename."""
        with pytest.raises(ValueError):
            extract_datetime_from_filename("bav_analysis_INVALID_104022.csv")
            
    def test_empty_filename(self):
        """Test empty filename."""
        with pytest.raises(ValueError):
            extract_datetime_from_filename("")


class TestParseExpiryFromKey:
    """Test expiry parsing from instrument keys."""
    
    def test_future_key(self):
        """Test parsing future instrument key."""
        key = "XCME.ZN.SEP25"
        expiry = parse_expiry_from_key(key)
        assert expiry == "SEP25"
        
    def test_option_key_standard(self):
        """Test parsing standard option key."""
        key = "XCME.WY3.16JUL25.111.C"
        expiry = parse_expiry_from_key(key)
        assert expiry == "16JUL25"
        
    def test_option_key_with_colon_strike(self):
        """Test parsing option key with colon in strike."""
        key = "XCME.ZN3.16SEP25.112:75.P"
        expiry = parse_expiry_from_key(key)
        assert expiry == "16SEP25"
        
    def test_invalid_key_format(self):
        """Test invalid key format returns None."""
        assert parse_expiry_from_key("INVALID") is None
        assert parse_expiry_from_key("XCME.ZN") is None  # Too few parts
        
    def test_empty_key(self):
        """Test empty key returns None."""
        assert parse_expiry_from_key("") is None
        assert parse_expiry_from_key(None) is None
        
    def test_non_string_key(self):
        """Test non-string key returns None."""
        assert parse_expiry_from_key(123) is None
        assert parse_expiry_from_key([]) is None


class TestParseSpotRiskCSV:
    """Test CSV parsing functionality."""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content."""
        return """key,bid,ask,strike,itype,vol,delta,gamma,vega,theta,last,net
VAR_STRING,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_STRING,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_PRICE,VAR_INT32
XCME.ZN.SEP25,110.5,110.75,0,future,0,1,0,0,0,110.625,100
XCME.WY3.16JUL25.111.C,1.5,1.75,111,call,0.25,0.45,0.02,0.15,-0.05,1.625,-50
XCME.ZN3.16SEP25.112:75.P,2.0,2.25,112.75,put,0.3,-0.35,0.025,0.18,-0.06,2.125,25"""
    
    @pytest.fixture
    def temp_csv_file(self, sample_csv_content):
        """Create temporary CSV file with sample content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
        
    def test_parse_valid_csv(self, temp_csv_file):
        """Test parsing valid CSV file."""
        df = parse_spot_risk_csv(temp_csv_file)
        
        # Check basic properties
        assert len(df) == 3
        assert 'midpoint_price' in df.columns
        assert 'expiry_date' in df.columns
        
        # Check that futures come first after sorting
        assert df.iloc[0]['itype'] == 'future'
        
        # Check midpoint calculations (find rows by key to be independent of sort order)
        future_row = df[df['key'] == 'XCME.ZN.SEP25'].iloc[0]
        call_row = df[df['key'] == 'XCME.WY3.16JUL25.111.C'].iloc[0]
        put_row = df[df['key'] == 'XCME.ZN3.16SEP25.112:75.P'].iloc[0]
        
        assert future_row['midpoint_price'] == (110.5 + 110.75) / 2
        assert call_row['midpoint_price'] == (1.5 + 1.75) / 2
        assert put_row['midpoint_price'] == (2.0 + 2.25) / 2
        
        # Check expiry parsing
        assert future_row['expiry_date'] == 'SEP25'
        assert call_row['expiry_date'] == '16JUL25'
        assert put_row['expiry_date'] == '16SEP25'
        
    def test_parse_missing_columns(self):
        """Test parsing CSV with missing columns."""
        content = """key,last,net
VAR_STRING,VAR_PRICE,VAR_INT32
XCME.ZN.SEP25,110.625,100"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
            
        try:
            df = parse_spot_risk_csv(temp_path)
            # Should still work but without midpoint_price
            assert len(df) == 1
            assert 'midpoint_price' not in df.columns
            assert 'expiry_date' in df.columns
        finally:
            os.unlink(temp_path)
            
    def test_parse_empty_csv(self):
        """Test parsing empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name
            
        try:
            with pytest.raises(ValueError, match="CSV file is empty"):
                parse_spot_risk_csv(temp_path)
        finally:
            os.unlink(temp_path)
            
    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_spot_risk_csv("nonexistent_file.csv")
            
    def test_parse_handles_exceptions(self):
        """Test that parser handles various edge cases gracefully."""
        # CSV with only headers
        content = """key,bid,ask,strike,itype
VAR_STRING,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_STRING"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
            
        try:
            df = parse_spot_risk_csv(temp_path)
            assert len(df) == 0  # No data rows
            assert 'midpoint_price' in df.columns
            assert 'expiry_date' in df.columns
        finally:
            os.unlink(temp_path)
            
    def test_sorting_priority(self):
        """Test that sorting follows correct priority."""
        content = """key,bid,ask,strike,itype
VAR_STRING,VAR_DOUBLE,VAR_DOUBLE,VAR_DOUBLE,VAR_STRING
XCME.ZN3.16SEP25.113.C,1.0,1.1,113,call
XCME.ZN3.16SEP25.112.C,1.2,1.3,112,call
XCME.ZN.SEP25,110.0,110.1,0,future
XCME.WY3.16JUL25.111.C,1.5,1.6,111,call
XCME.ZN.DEC25,109.0,109.1,0,future"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
            
        try:
            df = parse_spot_risk_csv(temp_path)
            
            # Check that futures come first
            assert df.iloc[0]['itype'] == 'future'
            assert df.iloc[1]['itype'] == 'future'
            
            # Check that within options, they're sorted by expiry then strike
            option_df = df[df['itype'] == 'call']
            strikes = option_df['strike'].tolist()
            assert strikes == sorted(strikes)  # Should be in ascending order
            
        finally:
            os.unlink(temp_path) 