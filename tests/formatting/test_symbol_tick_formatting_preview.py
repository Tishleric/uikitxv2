import os
import sys

import pytest

try:
    from lib.trading.common.price_parser import decimal_to_tt_bond_format_by_symbol
except ModuleNotFoundError:
    # Allow running directly via `python tests/.../test_symbol_tick_formatting_preview.py`
    CURRENT_DIR = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from lib.trading.common.price_parser import decimal_to_tt_bond_format_by_symbol


@pytest.mark.parametrize(
    "symbol, decimal_price, expected",
    [
        # Halves (ZN/TY, ZB/US)
        ("TYU5", 112 + 10.5 / 32.0, "112'105"),
        ("USU5", 117 + 3.0 / 32.0, "117'030"),
        # Quarters (ZT/TU)
        ("TUU5", 112 + 10.25 / 32.0, "112'1025"),
        ("ZTZ5 Comdty", 110 + 8.75 / 32.0, "110'0875"),
        # Eighths (ZF/FV)
        ("FVU5", 111 + 7.625 / 32.0, "111'0762"),
        ("ZFZ5", 110 + 8.875 / 32.0, "110'0887"),
        # Rollover edge (exact midpoint between 31.5 and 32.0 → rounds to 32.0)
        ("TYU5", 109 + 31.75 / 32.0, "110'000"),
    ],
)
def test_symbol_aware_tick_format_preview(symbol: str, decimal_price: float, expected: str):
    result = decimal_to_tt_bond_format_by_symbol(decimal_price, symbol)
    print(f"symbol={symbol} decimal={decimal_price} -> tick={result}")
    assert result == expected


if __name__ == "__main__":
    # Allow simple "python tests/formatting/test_symbol_tick_formatting_preview.py" execution
    cases = [
        ("TYU5", 112 + 10.5 / 32.0),
        ("USU5", 117 + 3.0 / 32.0),
        ("TUU5", 112 + 10.25 / 32.0),
        ("ZTZ5 Comdty", 110 + 8.75 / 32.0),
        ("FVU5", 111 + 7.625 / 32.0),
        ("ZFZ5", 110 + 8.875 / 32.0),
        ("TYU5", 109 + 31.75 / 32.0),
    ]
    for sym, dp in cases:
        out = decimal_to_tt_bond_format_by_symbol(dp, sym)
        print(f"symbol={sym} decimal={dp} -> tick={out}")

