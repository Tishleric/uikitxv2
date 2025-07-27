#!/usr/bin/env python3
"""Inline parity test for translators."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Test 1: Import all translators
print("Testing translator imports...")
try:
    from lib.trading.market_prices.rosetta_stone import RosettaStone
    from lib.trading.symbol_translator import SymbolTranslator
    from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator
    print("SUCCESS: All translators imported")
except Exception as e:
    print(f"ERROR importing: {e}")
    sys.exit(1)

# Test 2: Initialize translators
print("\nInitializing translators...")
try:
    rosetta = RosettaStone()
    symbol_translator = SymbolTranslator()
    spot_risk_translator = SpotRiskSymbolTranslator()
    print("SUCCESS: All translators initialized")
except Exception as e:
    print(f"ERROR initializing: {e}")
    sys.exit(1)

# Test 3: Compare ActantTrades translations
print("\n" + "="*60)
print("ACTANTTRADES FORMAT COMPARISON")
print("="*60)

test_trades = [
    "XCMEOCADPS20250721N0VY3/111",
    "XCMEOCADPS20250728N0VY4/111.75",
    "XCMEOCADPS20250801Q0ZN1/111",
]

for symbol in test_trades:
    print(f"\nInput: {symbol}")
    
    # SymbolTranslator
    try:
        st_result = symbol_translator.translate(symbol)
    except Exception as e:
        st_result = f"ERROR: {e}"
    
    # RosettaStone
    try:
        rs_result = rosetta.translate(symbol, 'actanttrades', 'bloomberg')
    except Exception as e:
        rs_result = f"ERROR: {e}"
    
    print(f"  SymbolTranslator: {st_result}")
    print(f"  RosettaStone:     {rs_result}")
    print(f"  Match: {'YES' if st_result == rs_result else 'NO'}")

# Test 4: Compare ActantRisk translations
print("\n" + "="*60)
print("ACTANTRISK FORMAT COMPARISON")
print("="*60)

test_risk = [
    "XCME.VY3.21JUL25.111.C",
    "XCME.ZN1.01AUG25.111.C",
    "XCME.OZN.AUG25.111.C",
]

for symbol in test_risk:
    print(f"\nInput: {symbol}")
    
    # SpotRiskSymbolTranslator
    try:
        srt_result = spot_risk_translator.translate(symbol)
    except Exception as e:
        srt_result = f"ERROR: {e}"
    
    # RosettaStone
    try:
        rs_result = rosetta.translate(symbol, 'actantrisk', 'bloomberg')
    except Exception as e:
        rs_result = f"ERROR: {e}"
    
    print(f"  SpotRiskTranslator: {srt_result}")
    print(f"  RosettaStone:       {rs_result}")
    print(f"  Match: {'YES' if srt_result == rs_result else 'NO'}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60) 