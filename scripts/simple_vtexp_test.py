#!/usr/bin/env python3
"""Simple test for vtexp loading."""

import sys
sys.path.append('.')

from pathlib import Path
import pandas as pd

# Test 1: Load vtexp CSV directly
print("Loading vtexp CSV...")
vtexp_file = Path("data/input/vtexp/vtexp_20250721_130437.csv")
if vtexp_file.exists():
    vtexp_df = pd.read_csv(vtexp_file)
    print(f"Found {len(vtexp_df)} entries")
    print("\nFirst 5 entries:")
    print(vtexp_df.head())
else:
    print("vtexp file not found!")

# Test 2: Check spot risk symbols
print("\n\nChecking spot risk symbols...")
spot_risk_file = Path("data/input/actant_spot_risk/2025-07-24/bav_analysis_20250723_170920.csv")
if spot_risk_file.exists():
    df = pd.read_csv(spot_risk_file)
    df = df.iloc[1:].reset_index(drop=True)  # Skip type row
    print(f"Found {len(df)} rows")
    print("\nColumn names:")
    print(df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
else:
    print("Spot risk file not found!")

# Test 3: Simple pattern matching
print("\n\nTesting pattern matching:")
test_spot_risk = "XCME.VY3.21JUL25.111.C"
test_vtexp = "XCME.ZN.N.G.21JUL25"

import re
spot_pattern = re.compile(r'XCME\.[A-Z]+\d?\.(\d{0,2}[A-Z]{3}\d{2})\.')
vtexp_pattern = re.compile(r'XCME\.[A-Z]+\.N\.G\.(\d{0,2}[A-Z]{3}\d{2})')

spot_match = spot_pattern.search(test_spot_risk)
vtexp_match = vtexp_pattern.search(test_vtexp)

print(f"Spot risk '{test_spot_risk}' -> expiry: {spot_match.group(1) if spot_match else 'NO MATCH'}")
print(f"vtexp '{test_vtexp}' -> expiry: {vtexp_match.group(1) if vtexp_match else 'NO MATCH'}") 