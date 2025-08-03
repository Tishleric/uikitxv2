"""
Test script to diagnose RosettaStone translation issues.
"""

import re

# Current regex (WRONG - only handles calls)
current_pattern = re.compile(
    r'XCMEOCADPS(\d{8})([A-Z])0([A-Z]{2,3})(\d*)(?:/(\d+(?:\.\d+)?))?'
)

# Fixed regex (handles both calls and puts)
fixed_pattern = re.compile(
    r'XCMEO([CP])ADPS(\d{8})([A-Z])0([A-Z]{2,3})(\d*)(?:/(\d+(?:\.\d+)?))?'
)

# Test symbols
test_symbols = [
    "XCMEOCADPS20250806Q0WY1/112.5",  # Call - should work with both
    "XCMEOPADPS20250805Q0GY1/110.5",  # Put - only works with fixed
]

print("TESTING CURRENT PATTERN (calls only):")
print("-" * 50)
for symbol in test_symbols:
    match = current_pattern.match(symbol)
    if match:
        print(f"✓ {symbol} - MATCHED")
        print(f"  Groups: {match.groups()}")
    else:
        print(f"✗ {symbol} - NO MATCH")

print("\nTESTING FIXED PATTERN (calls and puts):")
print("-" * 50)
for symbol in test_symbols:
    match = fixed_pattern.match(symbol)
    if match:
        print(f"✓ {symbol} - MATCHED")
        print(f"  Groups: {match.groups()}")
        option_type = match.group(1)
        print(f"  Option type: {'Call' if option_type == 'C' else 'Put'}")
    else:
        print(f"✗ {symbol} - NO MATCH")

print("\nDIAGNOSIS:")
print("-" * 50)
print("The issue is that the regex pattern in rosetta_stone.py line 77:")
print("  r'XCMEOCADPS(\\d{8})([A-Z])0([A-Z]{2,3})(\\d*)(?:/(\\d+(?:\\.\\d+)?))?'")
print("\nIt literally looks for 'XCMEOCADPS' which only matches calls.")
print("Put options have 'XCMEOPADPS' (P instead of C).")
print("\nThe fix is to change the pattern to:")
print("  r'XCMEO([CP])ADPS(\\d{8})([A-Z])0([A-Z]{2,3})(\\d*)(?:/(\\d+(?:\\.\\d+)?))?'")
print("\nThis captures the option type (C or P) as a group.")