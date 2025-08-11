#!/usr/bin/env python3
"""Quick test of the multiple COMB case"""

import re

def proposed_logic(symbol):
    """Proposed improved logic"""
    # Get symbol - already in Bloomberg format
    symbol = str(symbol).strip()
    
    # Skip invalid or empty symbols
    if not symbol or symbol == 'nan' or symbol == '0.0':
        return None
    
    # Remove ALL occurrences of COMB with flexible spacing
    # The + after the pattern means one or more occurrences
    symbol = re.sub(r'(\s+COMB\s+)+', ' ', symbol)
    
    # Also handle COMB at start or end
    symbol = re.sub(r'^COMB\s+', '', symbol)
    symbol = re.sub(r'\s+COMB$', '', symbol)
    
    # Normalize multiple spaces to single space
    symbol = re.sub(r'\s+', ' ', symbol)
    
    # Strip again in case of edge spaces
    symbol = symbol.strip()
    
    return symbol

# Test the specific case
test = "TYWQ25P1 COMB 110 COMB Comdty"
print(f"Input:  '{test}'")
print(f"Output: '{proposed_logic(test)}'")

# Debug steps
symbol = test.strip()
print(f"\nStep 1 - After strip: '{symbol}'")

symbol = re.sub(r'(\s+COMB\s+)+', ' ', symbol)
print(f"Step 2 - After COMB removal: '{symbol}'")

symbol = re.sub(r'^COMB\s+', '', symbol)
print(f"Step 3 - After start COMB: '{symbol}'")

symbol = re.sub(r'\s+COMB$', '', symbol)
print(f"Step 4 - After end COMB: '{symbol}'")

symbol = re.sub(r'\s+', ' ', symbol)
print(f"Step 5 - After space norm: '{symbol}'")

symbol = symbol.strip()
print(f"Step 6 - Final: '{symbol}'")