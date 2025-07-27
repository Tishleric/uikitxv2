#!/usr/bin/env python3
"""Quick test of RosettaStone functionality."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    translator = RosettaStone()
    
    # Test ActantRisk to Bloomberg
    test_symbol = "XCME.VY3.21JUL25.111.C"
    print(f"Testing ActantRisk: {test_symbol}")
    result = translator.translate(test_symbol, 'actantrisk', 'bloomberg')
    print(f"  Result: {result}")
    
    # Test ActantTrades parsing
    test_trades = "XCMEOCADPS20250728N0VY4/111"
    print(f"\nTesting ActantTrades: {test_trades}")
    result = translator.translate(test_trades, 'actanttrades', 'bloomberg')
    print(f"  Result: {result}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 