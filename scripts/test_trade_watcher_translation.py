#!/usr/bin/env python3
"""
Test symbol translation for trade ledger watcher
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.market_prices.rosetta_stone import RosettaStone

# Test futures symbol from trade ledger
futures_symbol = "XCMEFFDPSX20250919U0ZN"

translator = RosettaStone()

# Try to translate
try:
    result = translator.translate(futures_symbol, 'actanttrades', 'bloomberg')
    print(f"Translation successful:")
    print(f"  Input: {futures_symbol}")
    print(f"  Output: {result}")
except Exception as e:
    print(f"Translation failed for: {futures_symbol}")
    print(f"  Error: {e}")
    
    # Let's also check if this is a futures contract
    print("\nAnalyzing symbol...")
    if futures_symbol.startswith('XCMEFFDPS'):
        print("  This appears to be an Actant futures symbol")
        print("  Format: XCMEFFDPSX{date}{month}{?}{series}")
        
        # Try to parse it manually
        import re
        match = re.match(r'XCMEFFDPSX(\d{8})([A-Z])(\d)([A-Z]{2})', futures_symbol)
        if match:
            groups = match.groups()
            print(f"  Parsed: date={groups[0]}, month_code={groups[1]}, ?={groups[2]}, series={groups[3]}")
            print("  Note: Futures may need special handling for Bloomberg format")
    
# Show a few option examples that should work
print("\nTesting option symbols from trade ledger format:")
option_symbols = [
    "XCMEOCADPS20250721N0VY00/111.5",
    "XCMEOCADPS20250714Z0ZN00/111.5"
]

for symbol in option_symbols:
    try:
        result = translator.translate(symbol, 'actanttrades', 'bloomberg')
        print(f"  {symbol} -> {result}")
    except Exception as e:
        print(f"  {symbol} -> FAILED: {e}") 