#!/usr/bin/env python3
"""Test specific broker translations that should work based on our calendar."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    rs = RosettaStone()
    
    # Test with actual broker symbols from the trades
    test_symbols = [
        # These are from the broker trades we analyzed
        ('"SEP 25 CBT 10YR TNOTE"', "broker", "cme"),
        ('"SEP 25 CBT 30YR TBOND"', "broker", "cme"),
        
        # Test a weekly option translation  
        ('WY1Q5 C11225', "cme", "broker"),
        
        # Test reverse translation
        ('ZNU5', "cme", "broker"),
    ]
    
    print("Testing Specific Broker Translations")
    print("="*50)
    
    for symbol, from_fmt, to_fmt in test_symbols:
        try:
            result = rs.translate(symbol, from_fmt, to_fmt)
            print(f"✓ {from_fmt} -> {to_fmt}:")
            print(f"  Input:  {symbol}")
            print(f"  Output: {result}")
            print()
        except Exception as e:
            print(f"✗ {from_fmt} -> {to_fmt}:")
            print(f"  Input:  {symbol}")
            print(f"  Error:  {e}")
            print()

if __name__ == "__main__":
    main()