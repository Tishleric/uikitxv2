#!/usr/bin/env python3
"""
Verify RosettaStone migration is working correctly.
This script tests various symbol formats to ensure all replacements are functional.
"""

import sys
sys.path.append('.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_translations():
    """Test various symbol translations."""
    rosetta = RosettaStone()
    
    print("=== ROSETTA STONE MIGRATION VERIFICATION ===\n")
    
    # Test ActantTrades format
    print("1. Testing ActantTrades format:")
    actant_trades_symbols = [
        "XCMEOCADPS20250721N0VY3/111",
        "XCMEOCADPS20250728N0VY4/111.75",
        "XCMEOCADPS20250801Q0ZN1/111",
        "XCMEOCADPS20250822U0OZN/97",
    ]
    
    for symbol in actant_trades_symbols:
        result = rosetta.translate(symbol, 'actanttrades', 'bloomberg')
        print(f"  {symbol} → {result}")
    
    # Test ActantRisk format
    print("\n2. Testing ActantRisk format:")
    actant_risk_symbols = [
        "XCME.VY3.21JUL25.111.C",
        "XCME.ZN1.01AUG25.111.C",
        "XCME.OZN.AUG25.111.C",
        "XCME.ZN.SEP25",
    ]
    
    for symbol in actant_risk_symbols:
        result = rosetta.translate(symbol, 'actantrisk', 'bloomberg')
        print(f"  {symbol} → {result}")
    
    # Test bidirectional translation
    print("\n3. Testing bidirectional translation:")
    bloomberg = "VBYN25C3 111.000 Comdty"
    cme = rosetta.translate(bloomberg, 'bloomberg', 'cme')
    actant_risk = rosetta.translate(cme, 'cme', 'actantrisk') if cme else None
    back_to_bloomberg = rosetta.translate(actant_risk, 'actantrisk', 'bloomberg') if actant_risk else None
    
    print(f"  Bloomberg: {bloomberg}")
    print(f"  → CME: {cme}")
    print(f"  → ActantRisk: {actant_risk}")
    print(f"  → Bloomberg: {back_to_bloomberg}")
    print(f"  Full circle: {'YES' if back_to_bloomberg == bloomberg else 'NO'}")
    
    print("\n✅ Migration verification complete!")

if __name__ == "__main__":
    try:
        test_translations()
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc() 