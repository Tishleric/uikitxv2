#!/usr/bin/env python3
"""Simple translator parity test."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone
from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator

print("TRANSLATOR PARITY TEST REPORT")
print("=" * 60)

# Initialize translators
rosetta = RosettaStone()
symbol_translator = SymbolTranslator()
spot_risk_translator = SpotRiskSymbolTranslator()

# Test 1: SymbolTranslator vs RosettaStone for ActantTrades
print("\n1. TESTING ActantTrades Format (SymbolTranslator vs RosettaStone)")
print("-" * 60)

test_cases_trades = [
    ("XCMEOCADPS20250721N0VY3/111", "Monday week 3"),
    ("XCMEOCADPS20250728N0VY4/111.75", "Monday week 4"),
    ("XCMEOCADPS20250729N0GY5/110.5", "Tuesday week 5"),
    ("XCMEOCADPS20250730N0WY5/111.25", "Wednesday week 5"),
    ("XCMEOCADPS20250801Q0ZN1/111", "Friday week 1"),
    ("XCMEOCADPS20250822U0OZN/97", "Quarterly"),
]

matches = 0
total = 0

for symbol, desc in test_cases_trades:
    total += 1
    print(f"\n{desc}: {symbol}")
    
    # SymbolTranslator
    try:
        st_result = symbol_translator.translate(symbol)
    except Exception as e:
        st_result = f"ERROR: {str(e)}"
    
    # RosettaStone
    try:
        rs_result = rosetta.translate(symbol, 'actanttrades', 'bloomberg')
    except Exception as e:
        rs_result = f"ERROR: {str(e)}"
    
    print(f"  SymbolTranslator: {st_result}")
    print(f"  RosettaStone:     {rs_result}")
    
    if st_result == rs_result:
        print(f"  Match: YES")
        matches += 1
    else:
        print(f"  Match: NO - MISMATCH!")

print(f"\nActantTrades Match Rate: {matches}/{total} ({(matches/total)*100:.0f}%)")

# Test 2: SpotRiskSymbolTranslator vs RosettaStone
print("\n\n2. TESTING ActantRisk Format (SpotRiskTranslator vs RosettaStone)")
print("-" * 60)

test_cases_spot = [
    ("XCME.VY3.21JUL25.111.C", "Monday Call"),
    ("XCME.VY3.21JUL25.111:75.P", "Monday Put fractional"),
    ("XCME.ZN1.01AUG25.111.C", "Friday Call"),
    ("XCME.OZN.AUG25.111.C", "Quarterly Call"),
    ("XCME.ZN.SEP25", "Futures"),
]

matches_spot = 0
total_spot = 0

for symbol, desc in test_cases_spot:
    total_spot += 1
    print(f"\n{desc}: {symbol}")
    
    # SpotRiskSymbolTranslator
    try:
        srt_result = spot_risk_translator.to_bloomberg(symbol)
    except Exception as e:
        srt_result = f"ERROR: {str(e)}"
    
    # RosettaStone
    try:
        rs_result = rosetta.translate(symbol, 'actantrisk', 'bloomberg')
    except Exception as e:
        rs_result = f"ERROR: {str(e)}"
    
    print(f"  SpotRiskTranslator: {srt_result}")
    print(f"  RosettaStone:       {rs_result}")
    
    if srt_result == rs_result:
        print(f"  Match: YES")
        matches_spot += 1
    else:
        print(f"  Match: NO - MISMATCH!")

print(f"\nActantRisk Match Rate: {matches_spot}/{total_spot} ({(matches_spot/total_spot)*100:.0f}%)")

# Test 3: Bidirectional translation
print("\n\n3. TESTING Bidirectional Translation")
print("-" * 60)

test_symbol = "VBYN25C3 111.000 Comdty"
print(f"\nStarting with: {test_symbol}")

# Bloomberg → CME
cme = rosetta.translate(test_symbol, 'bloomberg', 'cme')
print(f"  → CME: {cme}")

# CME → ActantRisk
if cme and not cme.startswith("ERROR"):
    actant = rosetta.translate(cme, 'cme', 'actantrisk')
    print(f"  → ActantRisk: {actant}")
    
    # ActantRisk → Bloomberg
    if actant and not actant.startswith("ERROR"):
        back = rosetta.translate(actant, 'actantrisk', 'bloomberg')
        print(f"  → Bloomberg: {back}")
        
        if back == test_symbol:
            print(f"  Full circle: YES")
        else:
            print(f"  Full circle: NO")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"ActantTrades format: {matches}/{total} matches ({(matches/total)*100:.0f}%)")
print(f"ActantRisk format: {matches_spot}/{total_spot} matches ({(matches_spot/total_spot)*100:.0f}%)")

total_all = total + total_spot
matches_all = matches + matches_spot
print(f"\nOverall: {matches_all}/{total_all} matches ({(matches_all/total_all)*100:.0f}%)")

if matches_all < total_all:
    print("\nWARNING: Not all translations match! Review mismatches above.")
else:
    print("\nSUCCESS: All translations match! Safe to proceed with migration.") 