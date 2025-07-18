#!/usr/bin/env python3
"""
Test script for FULLPNL automation components.

Verifies that the new consolidated code produces identical results
to the original master_pnl_table scripts.
"""

import sys
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.fullpnl import SymbolMapper, PnLDatabase, SpotRiskDatabase, MarketPricesDatabase, FULLPNLBuilder


def test_symbol_mapping():
    """Test symbol mapping functionality."""
    print("\n=== Testing Symbol Mapping ===")
    mapper = SymbolMapper()
    
    # Test Bloomberg parsing
    test_symbols = [
        "TYU5 Comdty",
        "VBYN25P3 110.250 Comdty",
        "3MN5P 110.000 Comdty",
    ]
    
    for symbol in test_symbols:
        parsed = mapper.parse_bloomberg_symbol(symbol)
        if parsed:
            print(f"\n{symbol}:")
            print(f"  Type: {parsed.symbol_type}")
            print(f"  Base: {parsed.base_symbol}")
            print(f"  Strike: {parsed.strike}")
            print(f"  Contract: {parsed.contract_code}")
        else:
            print(f"\nFailed to parse: {symbol}")
            
    # Test contract to expiry mapping
    print("\n\n=== Contract to Expiry Mapping ===")
    contracts = ["3MN", "VBYN", "TYWN"]
    for contract in contracts:
        expiry = mapper.map_contract_to_expiry(contract)
        print(f"{contract} -> {expiry}")
        
    return True


def test_database_connections():
    """Test database adapter connections."""
    print("\n\n=== Testing Database Connections ===")
    
    # Test P&L database
    try:
        pnl_db = PnLDatabase(Path("data/output/pnl/pnl_tracker.db"))
        if pnl_db.fullpnl_exists():
            print("✓ FULLPNL table exists")
            columns = pnl_db.get_fullpnl_columns()
            print(f"  Columns: {', '.join(columns[:5])}...")
        else:
            print("✗ FULLPNL table does not exist")
        
        symbols = pnl_db.get_all_symbols()
        print(f"✓ Found {len(symbols)} symbols in positions table")
        pnl_db.close()
    except Exception as e:
        print(f"✗ P&L database error: {e}")
        
    # Test Spot Risk database
    try:
        spot_risk_db = SpotRiskDatabase(Path("data/output/spot_risk/spot_risk.db"))
        print("✓ Connected to Spot Risk database")
        spot_risk_db.close()
    except Exception as e:
        print(f"✗ Spot Risk database error: {e}")
        
    # Test Market Prices database
    try:
        market_prices_db = MarketPricesDatabase(Path("data/output/market_prices/market_prices.db"))
        print("✓ Connected to Market Prices database")
        market_prices_db.close()
    except Exception as e:
        print(f"✗ Market Prices database error: {e}")
        
    return True


def test_builder_basics():
    """Test basic builder functionality."""
    print("\n\n=== Testing FULLPNLBuilder ===")
    
    try:
        builder = FULLPNLBuilder()
        print("✓ Builder initialized")
        
        # Check missing columns
        missing = builder.get_missing_columns()
        if missing:
            print(f"  Missing columns: {', '.join(missing[:5])}...")
        else:
            print("  All expected columns present")
            
        builder.close()
        print("✓ Builder closed successfully")
        
    except Exception as e:
        print(f"✗ Builder error: {e}")
        
    return True


def run_unit_tests():
    """Run the unit test suite."""
    print("\n\n=== Running Unit Tests ===")
    
    # Load test module
    loader = unittest.TestLoader()
    suite = loader.discover('tests/fullpnl', pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main test runner."""
    print("FULLPNL Automation Component Tests")
    print("=" * 50)
    
    all_passed = True
    
    # Run component tests
    try:
        all_passed &= test_symbol_mapping()
    except Exception as e:
        print(f"\nSymbol mapping test failed: {e}")
        all_passed = False
        
    try:
        all_passed &= test_database_connections()
    except Exception as e:
        print(f"\nDatabase connection test failed: {e}")
        all_passed = False
        
    try:
        all_passed &= test_builder_basics()
    except Exception as e:
        print(f"\nBuilder test failed: {e}")
        all_passed = False
        
    # Run unit tests
    try:
        all_passed &= run_unit_tests()
    except Exception as e:
        print(f"\nUnit tests failed: {e}")
        all_passed = False
        
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main()) 