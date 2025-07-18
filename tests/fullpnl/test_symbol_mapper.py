"""
Unit tests for SymbolMapper class.

Compares outputs with the original parsing logic from master_pnl_table scripts.
"""

import unittest
from lib.trading.fullpnl.symbol_mapper import SymbolMapper, ParsedSymbol


class TestSymbolMapper(unittest.TestCase):
    """Test symbol format conversions."""
    
    def setUp(self):
        self.mapper = SymbolMapper()
        
    def test_parse_bloomberg_futures(self):
        """Test parsing Bloomberg future symbols."""
        # Test case from original scripts
        symbol = "TYU5 Comdty"
        parsed = self.mapper.parse_bloomberg_symbol(symbol)
        
        self.assertIsNotNone(parsed)
        assert parsed is not None  # Type guard for mypy
        self.assertEqual(parsed.symbol_type, 'FUT')
        self.assertEqual(parsed.base_symbol, 'TYU5')
        self.assertEqual(parsed.contract_code, 'TYU5')
        self.assertIsNone(parsed.strike)
        
    def test_parse_bloomberg_options(self):
        """Test parsing Bloomberg option symbols."""
        # Test cases from original scripts
        test_cases = [
            ("VBYN25P3 110.250 Comdty", 'PUT', 'VBYN25P3', 110.250, 'VBYN'),
            ("3MN5P 110.000 Comdty", 'PUT', '3MN5P', 110.000, '3MN'),
            ("TYWN25P4 109.750 Comdty", 'PUT', 'TYWN25P4', 109.750, 'TYWN'),
        ]
        
        for symbol, expected_type, expected_base, expected_strike, expected_contract in test_cases:
            with self.subTest(symbol=symbol):
                parsed = self.mapper.parse_bloomberg_symbol(symbol)
                
                self.assertIsNotNone(parsed)
                assert parsed is not None  # Type guard
                self.assertEqual(parsed.symbol_type, expected_type)
                self.assertEqual(parsed.base_symbol, expected_base)
                self.assertEqual(parsed.strike, expected_strike)
                self.assertEqual(parsed.contract_code, expected_contract)
                
    def test_parse_actant_futures(self):
        """Test parsing Actant future symbols."""
        symbol = "XCME.ZN.SEP25"
        parsed = self.mapper.parse_actant_symbol(symbol)
        
        self.assertIsNotNone(parsed)
        assert parsed is not None  # Type guard
        self.assertEqual(parsed.symbol_type, 'FUT')
        self.assertEqual(parsed.base_symbol, 'ZN')
        self.assertEqual(parsed.expiry, 'SEP25')
        
    def test_parse_actant_options(self):
        """Test parsing Actant option symbols."""
        # Test cases from original scripts
        test_cases = [
            ("XCME.ZN3.18JUL25.110:25.P", 'PUT', 'ZN3', 110.25, '18JUL25'),
            ("XCME.ZN3.18JUL25.110.C", 'CALL', 'ZN3', 110.0, '18JUL25'),
            ("XCME.ZN2.21JUL25.109:50.P", 'PUT', 'ZN2', 109.50, '21JUL25'),
        ]
        
        for symbol, expected_type, expected_base, expected_strike, expected_expiry in test_cases:
            with self.subTest(symbol=symbol):
                parsed = self.mapper.parse_actant_symbol(symbol)
                
                self.assertIsNotNone(parsed)
                assert parsed is not None  # Type guard
                self.assertEqual(parsed.symbol_type, expected_type)
                self.assertEqual(parsed.base_symbol, expected_base)
                self.assertEqual(parsed.strike, expected_strike)
                self.assertEqual(parsed.expiry, expected_expiry)
                
    def test_contract_to_expiry_mapping(self):
        """Test contract code to expiry date mapping."""
        # Test mappings discovered in original scripts
        test_cases = [
            ("3M", "18JUL25"),
            ("3MN", "18JUL25"),
            ("VBY", "21JUL25"),
            ("VBYN", "21JUL25"),
            ("TWN", "23JUL25"),
            ("TYWN", "23JUL25"),
        ]
        
        for contract, expected_expiry in test_cases:
            with self.subTest(contract=contract):
                expiry = self.mapper.map_contract_to_expiry(contract)
                self.assertEqual(expiry, expected_expiry)
                
        # Test with trailing digits
        self.assertEqual(self.mapper.map_contract_to_expiry("VBYN25"), "21JUL25")
        self.assertEqual(self.mapper.map_contract_to_expiry("3MN5"), "18JUL25")
        
    def test_strike_format_conversion(self):
        """Test strike price format conversions."""
        # Test decimal to colon
        self.assertEqual(self.mapper.convert_strike_format(110.25, to_colon=True), "110:25")
        self.assertEqual(self.mapper.convert_strike_format(110.0, to_colon=True), "110")
        self.assertEqual(self.mapper.convert_strike_format(109.75, to_colon=True), "109:75")
        
        # Test to decimal
        self.assertEqual(self.mapper.convert_strike_format(110.25, to_colon=False), "110.250")
        self.assertEqual(self.mapper.convert_strike_format(110.0, to_colon=False), "110.000")
        
    def test_symbol_matching(self):
        """Test matching Bloomberg and Actant symbols."""
        # Future match
        self.assertTrue(
            self.mapper.match_symbols("TYU5 Comdty", "XCME.ZN.SEP25")
        )
        
        # Option matches
        test_cases = [
            ("VBYN25P3 110.250 Comdty", "XCME.ZN3.21JUL25.110:25.P", True),
            ("3MN5P 110.000 Comdty", "XCME.ZN3.18JUL25.110.P", True),
            # Mismatches
            ("VBYN25P3 110.250 Comdty", "XCME.ZN3.21JUL25.110:25.C", False),  # PUT vs CALL
            ("VBYN25P3 110.250 Comdty", "XCME.ZN3.21JUL25.110.P", False),  # Different strike
        ]
        
        for bloom, actant, expected in test_cases:
            with self.subTest(bloom=bloom, actant=actant):
                result = self.mapper.match_symbols(bloom, actant)
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 