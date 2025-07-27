#!/usr/bin/env python3
"""Test futures translation with RosettaStone"""

import sys
sys.path.append('.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

rosetta = RosettaStone()

# Test translations
test_cases = [
    ("XCMEFFDPSX20250919U0ZN", "actanttrades", "bloomberg"),
    ("XCME.ZN.SEP25", "actantrisk", "bloomberg"),
    ("XCME.ZN.SEP25", "actantrisk", "cme"),
    ("TYU5 Comdty", "bloomberg", "actantrisk"),
    ("ZNU5", "cme", "actantrisk"),
]

print("Testing futures translations:\n")
for symbol, from_fmt, to_fmt in test_cases:
    result = rosetta.translate(symbol, from_fmt, to_fmt)
    print(f"{symbol} ({from_fmt}) → {to_fmt}: {result}") 