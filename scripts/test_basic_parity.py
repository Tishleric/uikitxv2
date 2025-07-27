#!/usr/bin/env python3
"""Quick test to verify translators are working."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Starting parity test...")

try:
    from lib.trading.market_prices.rosetta_stone import RosettaStone
    print("✓ RosettaStone imported")
except Exception as e:
    print(f"✗ Failed to import RosettaStone: {e}")
    sys.exit(1)

try:
    from lib.trading.symbol_translator import SymbolTranslator
    print("✓ SymbolTranslator imported")
except Exception as e:
    print(f"✗ Failed to import SymbolTranslator: {e}")
    sys.exit(1)

try:
    rosetta = RosettaStone()
    symbol_translator = SymbolTranslator()
    print("✓ Translators initialized")
except Exception as e:
    print(f"✗ Failed to initialize: {e}")
    sys.exit(1)

# Test a simple translation
test_symbol = "XCMEOCADPS20250721N0VY3/111"
print(f"\nTesting: {test_symbol}")

try:
    st_result = symbol_translator.translate(test_symbol)
    print(f"SymbolTranslator: {st_result}")
except Exception as e:
    print(f"SymbolTranslator ERROR: {e}")

try:
    rs_result = rosetta.translate(test_symbol, 'actanttrades', 'bloomberg')
    print(f"RosettaStone: {rs_result}")
except Exception as e:
    print(f"RosettaStone ERROR: {e}")

print("\nDone.") 