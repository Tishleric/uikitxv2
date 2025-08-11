#!/usr/bin/env python3
"""
Isolated test script for option symbol normalization
Tests current logic and proposed improvements without affecting any databases
"""

import re

# Test symbols provided by user
TEST_SYMBOLS = [
    "TJPQ25C1 110 Comdty",
    "TJPQ25C1 109.75 Comdty",
    "TJPQ25C1 109.5 Comdty",
    "TJPQ25C1 109.25 Comdty",
    "TYWQ25P1 115 COMB Comdty",
    "TYWQ25P1 114.75 COMB Comdty",
    "TYWQ25P1 114.5 COMB Comdty",
    "TYWQ25P1 114.25 COMB Comdty",
    "TYWQ25P1 114 COMB Comdty",
    "TYWQ25P1 113.75 COMB Comdty",
    "TYWQ25P1 113.5 COMB Comdty",
    "TYWQ25P1 113.25 COMB Comdty",
    "TYWQ25P1 113 COMB Comdty",
    "TYWQ25P1 112.75 COMB Comdty",
    "TYWQ25P1 112.5 COMB Comdty",
    "TYWQ25P1 112.25 COMB Comdty",
    "TYWQ25P1 112 COMB Comdty",
]

# Additional edge cases to test
EDGE_CASES = [
    "TYWQ25P1  115  COMB  Comdty",  # Multiple spaces
    "TYWQ25P1 115  COMB Comdty",     # Extra space before COMB
    "TYWQ25P1 115 COMB  Comdty",     # Extra space after COMB
    "COMB TYWQ25P1 115 Comdty",      # COMB at start
    "TYWQ25P1 115 Comdty COMB",      # COMB at end
    "TYWQ25P1 COMB 115 COMB Comdty", # Multiple COMB
    "  TYWQ25P1 115 COMB Comdty  ",  # Leading/trailing spaces
]


def current_normalization(symbol):
    """Current logic from close_price_watcher.py"""
    # Strip whitespace
    symbol = str(symbol).strip()
    
    # Remove 'COMB' if present (current logic)
    if ' COMB ' in symbol:
        symbol = symbol.replace(' COMB ', ' ')
    
    return symbol


def improved_normalization_v1(symbol):
    """Improved normalization with regex"""
    # Strip whitespace
    symbol = str(symbol).strip()
    
    # Remove COMB with flexible spacing
    symbol = re.sub(r'\s+COMB\s+', ' ', symbol)
    
    # Normalize multiple spaces to single space
    symbol = re.sub(r'\s+', ' ', symbol)
    
    return symbol


def improved_normalization_v2(symbol):
    """Alternative approach - handle COMB at any position"""
    # Strip whitespace
    symbol = str(symbol).strip()
    
    # Remove COMB as a complete word (with word boundaries)
    symbol = re.sub(r'\bCOMB\b', '', symbol)
    
    # Normalize multiple spaces to single space
    symbol = re.sub(r'\s+', ' ', symbol)
    
    # Strip again in case COMB was at start/end
    symbol = symbol.strip()
    
    return symbol


def test_normalizations():
    """Test all normalization approaches"""
    
    print("=" * 80)
    print("OPTION SYMBOL NORMALIZATION TEST")
    print("=" * 80)
    print()
    
    # Test with provided symbols
    print("TEST SET 1: User-provided symbols")
    print("-" * 80)
    print(f"{'Original':<35} {'Current':<30} {'Improved v1':<30} {'Improved v2':<30}")
    print("-" * 80)
    
    for symbol in TEST_SYMBOLS:
        current = current_normalization(symbol)
        improved1 = improved_normalization_v1(symbol)
        improved2 = improved_normalization_v2(symbol)
        
        print(f"{symbol:<35} {current:<30} {improved1:<30} {improved2:<30}")
    
    print()
    print("TEST SET 2: Edge cases")
    print("-" * 80)
    print(f"{'Original':<35} {'Current':<30} {'Improved v1':<30} {'Improved v2':<30}")
    print("-" * 80)
    
    for symbol in EDGE_CASES:
        current = current_normalization(symbol)
        improved1 = improved_normalization_v1(symbol)
        improved2 = improved_normalization_v2(symbol)
        
        # Use repr to show exact spacing
        print(f"{repr(symbol):<35} {current:<30} {improved1:<30} {improved2:<30}")
    
    print()
    print("ANALYSIS:")
    print("-" * 80)
    
    # Check for consistency
    issues_found = []
    
    for symbols in [TEST_SYMBOLS, EDGE_CASES]:
        for symbol in symbols:
            current = current_normalization(symbol)
            improved1 = improved_normalization_v1(symbol)
            improved2 = improved_normalization_v2(symbol)
            
            # Check if current method leaves extra spaces
            if '  ' in current:
                issues_found.append(f"Current method leaves double spaces in: {repr(symbol)}")
            
            # Check if COMB not removed in edge cases
            if 'COMB' in current and 'COMB' in symbol:
                issues_found.append(f"Current method doesn't remove COMB from: {repr(symbol)}")
    
    if issues_found:
        print("Issues found with current normalization:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("No issues found with current normalization on standard cases.")
    
    print()
    print("RECOMMENDATIONS:")
    print("-" * 80)
    print("1. Current method works well for standard cases but fails on edge cases")
    print("2. Improved v1 handles flexible spacing around COMB")
    print("3. Improved v2 removes COMB anywhere in the string")
    print("4. For production, recommend Improved v1 as it preserves COMB position logic")
    

if __name__ == "__main__":
    test_normalizations()