"""
Test script to verify the RosettaStone fix for put options.
"""

from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_translation():
    rs = RosettaStone()
    
    test_cases = [
        ("XCMEOCADPS20250806Q0WY1/112.5", "Call option"),
        ("XCMEOPADPS20250805Q0GY1/110.5", "Put option"),
        ("XCMEFFDPSX20250919U0ZN", "Futures contract"),
    ]
    
    print("Testing RosettaStone translations after fix:")
    print("=" * 70)
    
    for symbol, description in test_cases:
        print(f"\n{description}: {symbol}")
        try:
            result = rs.translate(symbol, 'actanttrades', 'bloomberg')
            if result:
                print(f"  ✓ Success: {result}")
            else:
                print(f"  ✗ Failed: No translation found")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Fix verification complete!")

if __name__ == '__main__':
    test_translation()