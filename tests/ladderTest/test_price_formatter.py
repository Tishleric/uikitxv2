import math

import pytest

from ladderTest.price_formatter import decimal_to_tt_bond_format
from ladderTest.scenario_ladder_v1 import convert_tt_special_format_to_decimal


@pytest.mark.parametrize(
    "decimal", [0.0, 0.015625, 1.0, 1.515625, 110.0, 110.015625, 110.03125, 109.984375]
)
def test_round_trip_conversion(decimal: float) -> None:
    """Convert decimal to TT string and back, verifying identity."""
    special = decimal_to_tt_bond_format(decimal)
    result = convert_tt_special_format_to_decimal(special)
    assert result is not None
    assert math.isclose(result, decimal, rel_tol=1e-9)


@pytest.mark.parametrize(
    "price_str,expected",
    [
        ("110'085", 110 + 8.5 / 32),
        ("110'0875", 110 + 8.75 / 32),
        ("110'08", 110 + 8 / 32),
        ("0'005", 0.015625),
    ],
)
def test_convert_tt_special_format_to_decimal(price_str: str, expected: float) -> None:
    """Verify parsing of explicit TT bond price strings."""
    result = convert_tt_special_format_to_decimal(price_str)
    assert result is not None
    assert math.isclose(result, expected, rel_tol=1e-9)


def test_invalid_inputs() -> None:
    """Invalid input cases return None or raise TypeError."""
    assert convert_tt_special_format_to_decimal("bad") is None
    with pytest.raises(TypeError):
        decimal_to_tt_bond_format("bad")

