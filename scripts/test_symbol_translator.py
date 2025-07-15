"""
Test the Symbol Translator with various dates and series
"""

import sys
sys.path.append('..')

from lib.trading.symbol_translator import SymbolTranslator
from datetime import datetime
import calendar

def test_symbol_translator():
    translator = SymbolTranslator()
    
    # Test cases with expected results based on July 2025 calendar
    test_cases = [
        # Monday July 14 (2nd Monday) - VY series
        ("XCMEOCADPS20250714N0VY2/108.75", "VBYN25C2 108.75 Comdty"),
        ("XCMEOPADPS20250714N0VY2/109.5", "VBYN25P2 109.5 Comdty"),
        
        # Tuesday July 15 (3rd Tuesday) - TJ series  
        ("XCMEOCADPS20250715N0TJ3/110.25", "TJPN25C3 110.25 Comdty"),
        
        # Wednesday July 16 (3rd Wednesday) - WY series
        ("XCMEOCADPS20250716N0WY3/111.0", "TYWN25C3 111 Comdty"),
        
        # Thursday July 17 (3rd Thursday) - TH series
        ("XCMEOCADPS20250717N0TH3/110.75", "TJWN25C3 110.75 Comdty"),
        
        # Friday July 18 (3rd Friday) - ZN series
        ("XCMEOCADPS20250718N0ZN3/111.5", "3MN5C 111.5 Comdty"),
        
        # Test other occurrences
        # Monday July 7 (1st Monday)
        ("XCMEOCADPS20250707N0VY1/109.0", "VBYN25C1 109 Comdty"),
        
        # Monday July 21 (3rd Monday)
        ("XCMEOCADPS20250721N0VY3/108.5", "VBYN25C3 108.5 Comdty"),
        
        # Monday July 28 (4th Monday)
        ("XCMEOCADPS20250728N0VY4/107.75", "VBYN25C4 107.75 Comdty"),
        
        # Test first week of July
        # Tuesday July 1 (1st Tuesday)
        ("XCMEOCADPS20250701N0TJ1/110.0", "TJPN25C1 110 Comdty"),
        
        # Wednesday July 2 (1st Wednesday)
        ("XCMEOCADPS20250702N0WY1/109.75", "TYWN25C1 109.75 Comdty"),
        
        # Thursday July 3 (1st Thursday)
        ("XCMEOCADPS20250703N0TH1/110.5", "TJWN25C1 110.5 Comdty"),
        
        # Friday July 4 (1st Friday)
        ("XCMEOCADPS20250704N0ZN1/111.25", "3MN5C 111.25 Comdty"),
    ]
    
    print("Testing Symbol Translator with corrected occurrence logic:")
    print("=" * 80)
    
    # Show July 2025 calendar for reference
    print("\nJuly 2025 Calendar:")
    print("Mo Tu We Th Fr")
    print("    1  2  3  4  (1st occurrence of each)")
    print(" 7  8  9 10 11  (1st Mon, 2nd Tue-Fri)")
    print("14 15 16 17 18  (2nd Mon, 3rd Tue-Fri)")
    print("21 22 23 24 25  (3rd Mon, 4th Tue-Fri)")
    print("28 29 30 31     (4th Mon, 5th Tue-Thu)")
    print()
    
    passed = 0
    failed = 0
    
    for actant_symbol, expected in test_cases:
        result = translator.translate(actant_symbol)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            passed += 1
        else:
            failed += 1
            
        print(f"{status}: {actant_symbol}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
    
    print(f"Summary: {passed} passed, {failed} failed")
    
    # Test with real trade data
    print("\n" + "=" * 80)
    print("Testing with actual trade symbols from trades_20250714.csv:")
    
    trade_symbols = [
        "XCMEOCADPS20250714N0VY2/108.75",
        "XCMEOCADPS20250714N0VY2/111",
        "XCMEOPADPS20250714N0VY2/109.5",
        "XCMEOPADPS20250714N0VY2/110.75",
    ]
    
    for symbol in trade_symbols:
        result = translator.translate(symbol)
        print(f"{symbol} -> {result}")

if __name__ == "__main__":
    test_symbol_translator() 