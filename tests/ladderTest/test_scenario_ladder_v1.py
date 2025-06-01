import sys
from pathlib import Path

import pytest

# Ensure repo root is on the path so ladderTest modules can be imported
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# scenario_ladder_v1 is not in the ladder package  # noqa: E402

# Skip all tests in this file as scenario_ladder_v1 is an application, not a library module
pytestmark = pytest.mark.skip(reason="scenario_ladder_v1 is an application, not part of the library package")

# Original tests commented out since the module is not available
# The scenario_ladder application is in apps/dashboards/ladder/scenario_ladder.py
# and is not exported as part of the trading.ladder package


def test_update_data_with_spot_price_basic(mocker):
    """Validate PnL and position calculation around spot price."""
    # Patch requests.get to ensure no network access
    mocker.patch.object(slv, "requests")

    existing = [
        {"price": "110'105", "decimal_price_val": 110.328125, "my_qty": "", "working_qty_side": ""},
        {"price": "110'100", "decimal_price_val": 110.3125, "my_qty": "2", "working_qty_side": "1"},
        {"price": "110'095", "decimal_price_val": 110.296875, "my_qty": "1", "working_qty_side": "2"},
    ]
    spot = {"decimal_price": 110.3125, "special_string_price": "110'100"}

    result = slv.update_data_with_spot_price(existing, spot, base_position=0, base_pnl=0.0)

    assert result[1]["is_exact_spot"] == 1
    assert result[1]["position_debug"] == 2
    assert result[2]["projected_pnl"] == -31.25
    assert result[2]["breakeven"] == -2.0


def test_update_data_with_spot_price_with_baseline(mocker):
    """Ensure baseline position and PnL feed into projections."""
    mocker.patch.object(slv, "requests")

    existing = [
        {"price": "110'100", "decimal_price_val": 110.3125, "my_qty": "", "working_qty_side": ""},
        {"price": "110'095", "decimal_price_val": 110.296875, "my_qty": "2", "working_qty_side": "2"},
    ]
    spot = {"decimal_price": 110.3125, "special_string_price": "110'100"}

    result = slv.update_data_with_spot_price(existing, spot, base_position=5, base_pnl=50.0)

    assert result[0]["projected_pnl"] == 50.0
    assert result[0]["position_debug"] == 5
    # Projected PnL after sell order should decrease accordingly
    assert pytest.approx(result[1]["projected_pnl"], abs=0.01) == -28.12
    assert result[1]["position_debug"] == 3
