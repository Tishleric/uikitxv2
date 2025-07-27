"""
Tests for RosettaStone - Universal symbol translator.

Tests all symbol formats, strike conversions, and edge cases.
"""

import pytest
from pathlib import Path

from lib.trading.market_prices.strike_converter import StrikeConverter
from lib.trading.market_prices.rosetta_stone import (
    RosettaStone,
    SymbolFormat,
    SymbolClass,
    ParsedSymbol
)


class TestStrikeConverter:
    """Test strike format conversions."""
    
    def test_xcme_to_decimal(self):
        """Test XCME colon notation to decimal conversion."""
        # Whole numbers
        assert StrikeConverter.xcme_to_decimal("111") == 111.0
        assert StrikeConverter.xcme_to_decimal("95") == 95.0
        
        # Fractional strikes
        assert StrikeConverter.xcme_to_decimal("111:25") == 111.25
        assert StrikeConverter.xcme_to_decimal("111:5") == 111.5  # Special case
        assert StrikeConverter.xcme_to_decimal("111:75") == 111.75
        
        # Edge cases
        assert StrikeConverter.xcme_to_decimal("0:5") == 0.5
        assert StrikeConverter.xcme_to_decimal("100:0") == 100.0
        
    def test_decimal_to_xcme(self):
        """Test decimal to XCME format conversion."""
        # Whole numbers
        assert StrikeConverter.decimal_to_xcme(111.0) == "111"
        assert StrikeConverter.decimal_to_xcme(95) == "95"
        
        # Fractional values
        assert StrikeConverter.decimal_to_xcme(111.25) == "111:25"
        assert StrikeConverter.decimal_to_xcme(111.5) == "111:5"  # Special case
        assert StrikeConverter.decimal_to_xcme(111.75) == "111:75"
        
        # String input
        assert StrikeConverter.decimal_to_xcme("111.5") == "111:5"
        
    def test_format_strike(self):
        """Test strike formatting for different systems."""
        # Bloomberg format (3 decimals)
        assert StrikeConverter.format_strike("111", "bloomberg") == "111.000"
        assert StrikeConverter.format_strike("111:5", "bloomberg") == "111.500"
        assert StrikeConverter.format_strike("111:75", "bloomberg") == "111.750"
        assert StrikeConverter.format_strike(111.25, "bloomberg") == "111.250"
        
        # CME format (integer basis points)
        assert StrikeConverter.format_strike("111", "cme") == "11100"
        assert StrikeConverter.format_strike("111:25", "cme") == "11125"
        assert StrikeConverter.format_strike("111:5", "cme") == "11150"
        assert StrikeConverter.format_strike("111:75", "cme") == "11175"
        
        # XCME format (preserves colon notation)
        assert StrikeConverter.format_strike("111", "xcme") == "111"
        assert StrikeConverter.format_strike(111.5, "xcme") == "111:5"
        assert StrikeConverter.format_strike("111.75", "xcme") == "111:75"
        
    def test_invalid_strikes(self):
        """Test error handling for invalid strikes."""
        with pytest.raises(ValueError):
            StrikeConverter.xcme_to_decimal("")
            
        with pytest.raises(ValueError):
            StrikeConverter.xcme_to_decimal("111:abc")
            
        with pytest.raises(ValueError):
            StrikeConverter.xcme_to_decimal("111:5:25")
            
        with pytest.raises(ValueError):
            StrikeConverter.format_strike("111", "invalid_format")


class TestRosettaStone:
    """Test symbol translator functionality."""
    
    @pytest.fixture
    def translator(self):
        """Create translator instance with test CSV."""
        # Assume CSV exists in expected location
        return RosettaStone()
        
    def test_classify_symbol(self, translator):
        """Test symbol classification."""
        # CME symbols
        assert translator.classify_symbol("VY3N5", SymbolFormat.CME) == SymbolClass.WEEKLY_MON_THU
        assert translator.classify_symbol("ZN1Q5", SymbolFormat.CME) == SymbolClass.WEEKLY_FRIDAY
        assert translator.classify_symbol("OZNQ5", SymbolFormat.CME) == SymbolClass.QUARTERLY
        
        # XCME symbols
        assert translator.classify_symbol("XCME.VY3.21JUL25.111.C", SymbolFormat.XCME) == SymbolClass.WEEKLY_MON_THU
        assert translator.classify_symbol("XCME.ZN1.01AUG25.111.P", SymbolFormat.XCME) == SymbolClass.WEEKLY_FRIDAY
        assert translator.classify_symbol("XCME.OZN.AUG25.111.C", SymbolFormat.XCME) == SymbolClass.QUARTERLY
        
        # Bloomberg symbols
        assert translator.classify_symbol("VBYN25C3 111.000 Comdty", SymbolFormat.BLOOMBERG) == SymbolClass.WEEKLY_MON_THU
        assert translator.classify_symbol("1MQ5C 111.000 Comdty", SymbolFormat.BLOOMBERG) == SymbolClass.WEEKLY_FRIDAY
        assert translator.classify_symbol("TYQ5C 111.000 Comdty", SymbolFormat.BLOOMBERG) == SymbolClass.QUARTERLY
        
    def test_parse_xcme_symbol(self, translator):
        """Test parsing XCME symbols."""
        # Weekly Mon-Thu
        parsed = translator.parse_symbol("XCME.VY3.21JUL25.111:75.C", SymbolFormat.XCME)
        assert parsed.base == "XCME.VY3.21JUL25"
        assert parsed.strike == "111:75"
        assert parsed.option_type == "C"
        assert parsed.symbol_class == SymbolClass.WEEKLY_MON_THU
        
        # Friday weekly
        parsed = translator.parse_symbol("XCME.ZN1.01AUG25.111:5.P", SymbolFormat.XCME)
        assert parsed.base == "XCME.ZN1.01AUG25"
        assert parsed.strike == "111:5"
        assert parsed.option_type == "P"
        assert parsed.symbol_class == SymbolClass.WEEKLY_FRIDAY
        
        # Quarterly
        parsed = translator.parse_symbol("XCME.OZN.AUG25.111:25.C", SymbolFormat.XCME)
        assert parsed.base == "XCME.OZN.AUG25"
        assert parsed.strike == "111:25"
        assert parsed.option_type == "C"
        assert parsed.symbol_class == SymbolClass.QUARTERLY
        
    def test_parse_cme_symbol(self, translator):
        """Test parsing CME symbols."""
        parsed = translator.parse_symbol("VY3N5 C11175", SymbolFormat.CME)
        assert parsed.base == "VY3N5"
        assert parsed.strike == "111.75"
        assert parsed.option_type == "C"
        
        parsed = translator.parse_symbol("OZNQ5 P11050", SymbolFormat.CME)
        assert parsed.base == "OZNQ5"
        assert parsed.strike == "110.5"
        assert parsed.option_type == "P"
        
    def test_parse_bloomberg_symbol(self, translator):
        """Test parsing Bloomberg symbols."""
        # Weekly Mon-Thu
        parsed = translator.parse_symbol("VBYN25C3 111.750 Comdty", SymbolFormat.BLOOMBERG)
        assert parsed.base == "VBYN25C3"
        assert parsed.strike == "111.750"
        assert parsed.option_type == "C"
        
        # Friday weekly
        parsed = translator.parse_symbol("1MQ5P 111.500 Comdty", SymbolFormat.BLOOMBERG)
        assert parsed.base == "1MQ5P"
        assert parsed.strike == "111.500"
        assert parsed.option_type == "P"
        
        # Quarterly
        parsed = translator.parse_symbol("TYQ5C 111.250 Comdty", SymbolFormat.BLOOMBERG)
        assert parsed.base == "TYQ5C"
        assert parsed.strike == "111.250"
        assert parsed.option_type == "C"
        
    def test_translate_xcme_to_bloomberg(self, translator):
        """Test XCME to Bloomberg translation."""
        # Weekly Mon-Thu Call
        result = translator.translate(
            "XCME.VY3.21JUL25.111:75.C",
            "xcme",
            "bloomberg"
        )
        assert result == "VBYN25C3 111.750 Comdty"
        
        # Weekly Mon-Thu Put
        result = translator.translate(
            "XCME.VY3.21JUL25.111:75.P",
            "xcme",
            "bloomberg"
        )
        assert result == "VBYN25P3 111.750 Comdty"
        
        # Friday weekly
        result = translator.translate(
            "XCME.ZN1.01AUG25.111:5.C",
            "xcme",
            "bloomberg"
        )
        assert result == "1MQ5C 111.500 Comdty"
        
        # Quarterly
        result = translator.translate(
            "XCME.OZN.AUG25.111:25.C",
            "xcme",
            "bloomberg"
        )
        assert result == "TYQ5C 111.250 Comdty"
        
    def test_translate_bloomberg_to_xcme(self, translator):
        """Test Bloomberg to XCME translation."""
        result = translator.translate(
            "VBYN25C3 111.750 Comdty",
            "bloomberg",
            "xcme"
        )
        assert result == "XCME.VY3.21JUL25.111:75.C"
        
        result = translator.translate(
            "1MQ5P 111.500 Comdty",
            "bloomberg",
            "xcme"
        )
        assert result == "XCME.ZN1.01AUG25.111:5.P"
        
    def test_translate_cme_to_bloomberg(self, translator):
        """Test CME to Bloomberg translation."""
        result = translator.translate(
            "VY3N5 C11175",
            "cme",
            "bloomberg"
        )
        assert result == "VBYN25C3 111.750 Comdty"
        
        result = translator.translate(
            "OZNQ5 P11050",
            "cme",
            "bloomberg"
        )
        assert result == "TYQ5P 110.500 Comdty"
        
    def test_round_trip_translations(self, translator):
        """Test round-trip translations maintain accuracy."""
        # XCME -> Bloomberg -> XCME
        original = "XCME.VY3.21JUL25.111:75.C"
        bloomberg = translator.translate(original, "xcme", "bloomberg")
        back_to_xcme = translator.translate(bloomberg, "bloomberg", "xcme")
        assert back_to_xcme == original
        
        # CME -> Bloomberg -> CME
        original = "VY3N5 C11175"
        bloomberg = translator.translate(original, "cme", "bloomberg")
        back_to_cme = translator.translate(bloomberg, "bloomberg", "cme")
        assert back_to_cme == original
        
    def test_edge_cases(self, translator):
        """Test edge cases and error handling."""
        # Invalid format
        result = translator.translate("INVALID", "xcme", "bloomberg")
        assert result is None
        
        # Missing mapping (if symbol not in CSV)
        result = translator.translate("XCME.XXX.01JAN99.100.C", "xcme", "bloomberg")
        assert result is None
        
    def test_all_strike_formats(self, translator):
        """Test all XCME strike format variations."""
        test_cases = [
            ("XCME.VY3.21JUL25.111.C", "VBYN25C3 111.000 Comdty"),
            ("XCME.VY3.21JUL25.111:25.C", "VBYN25C3 111.250 Comdty"),
            ("XCME.VY3.21JUL25.111:5.C", "VBYN25C3 111.500 Comdty"),
            ("XCME.VY3.21JUL25.111:75.C", "VBYN25C3 111.750 Comdty"),
        ]
        
        for xcme, expected_bloomberg in test_cases:
            result = translator.translate(xcme, "xcme", "bloomberg")
            assert result == expected_bloomberg, f"Failed for {xcme}" 