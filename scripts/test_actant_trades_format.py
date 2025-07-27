#!/usr/bin/env python3
"""
Test ActantTrades format translation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone, SymbolFormat

def test_actant_trades_parsing():
    """Test parsing and translation of ActantTrades format."""
    translator = RosettaStone()
    
    # Test trades from trades_20250727.csv
    test_symbols = [
        "XCMEOCADPS20250728N0VY4/111",
        "XCMEOCADPS20250822U0OZN/97",
        "XCMEOCADPS20250730N0WY5/111.5",
        "XCMEOCADPS20250801Q0ZN1/112",
        "XCMEOCADPS20250808Q0ZN2/112",
    ]
    
    print("Testing ActantTrades format parsing and translation:")
    print("=" * 60)
    
    for symbol in test_symbols:
        print(f"\nActantTrades: {symbol}")
        try:
            # Parse the symbol
            parsed = translator.parse_symbol(symbol, SymbolFormat.ACTANT_TRADES)
            print(f"  Parsed base: {parsed.base}")
            print(f"  Strike: {parsed.strike}")
            print(f"  Option type: {parsed.option_type}")
            print(f"  Classification: {parsed.symbol_class}")
            
            # Try to translate to Bloomberg
            bloomberg = translator.translate(symbol, 'actanttrades', 'bloomberg')
            if bloomberg:
                print(f"  Bloomberg: {bloomberg}")
            else:
                print("  Bloomberg: Translation failed (mapping not found)")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Test futures format
    print("\n\nTesting ActantTrades futures format:")
    print("=" * 60)
    
    futures_symbol = "XCMEFFDPSX20250919U0ZN"
    print(f"\nActantTrades Futures: {futures_symbol}")
    try:
        parsed = translator.parse_symbol(futures_symbol, SymbolFormat.ACTANT_TRADES)
        print(f"  Parsed successfully: {parsed}")
    except Exception as e:
        print(f"  Expected error (futures not yet supported): {e}")


def test_actant_time_format():
    """Test ActantTime format from vtexp."""
    translator = RosettaStone()
    
    # Test symbols from vtexp_20250721_112507.csv
    test_symbols = [
        "XCME.ZN.N.G.21JUL25",
        "XCME.ZN.N.G.22JUL25",
        "XCME.ZN.N.G.23JUL25",
        "XCME.ZN.N.G.AUG25",
    ]
    
    print("\n\nTesting ActantTime format parsing:")
    print("=" * 60)
    
    for symbol in test_symbols:
        print(f"\nActantTime: {symbol}")
        try:
            parsed = translator.parse_symbol(symbol, SymbolFormat.ACTANT_TIME)
            print(f"  Parsed base: {parsed.base}")
            print(f"  Classification: {parsed.symbol_class}")
            
            # Try to translate to Bloomberg
            bloomberg = translator.translate(symbol, 'actanttime', 'bloomberg')
            if bloomberg:
                print(f"  Bloomberg: {bloomberg}")
            else:
                print("  Bloomberg: Translation failed (mapping not found)")
                
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    test_actant_trades_parsing()
    test_actant_time_format() 