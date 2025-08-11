import math
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this file directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.trading.actant.spot_risk.calculator import (
    SpotRiskGreekCalculator,
    DEFAULT_DV01,
    HEDGE_RATIOS,
)


def isclose(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def test_actantrisk_key_series_mapping_to_dv01():
    calc = SpotRiskGreekCalculator()

    # ZN baseline
    zn_key = "XCME.ZN.SEP25"
    zn_dv01 = calc._get_futures_dv01(zn_key)
    assert isclose(zn_dv01, DEFAULT_DV01)

    # ZF -> FV mapping
    zf_key = "XCME.ZF.SEP25"
    zf_dv01 = calc._get_futures_dv01(zf_key)
    expected_fv = DEFAULT_DV01 / HEDGE_RATIOS["FV"]
    assert isclose(zf_dv01, expected_fv)

    # ZT -> TU mapping
    zt_key = "XCME.ZT.SEP25"
    zt_dv01 = calc._get_futures_dv01(zt_key)
    expected_tu = DEFAULT_DV01 / HEDGE_RATIOS["TU"]
    assert isclose(zt_dv01, expected_tu)

    # ZB -> US mapping
    zb_key = "XCME.ZB.SEP25"
    zb_dv01 = calc._get_futures_dv01(zb_key)
    expected_us = DEFAULT_DV01 / HEDGE_RATIOS["US"]
    assert isclose(zb_dv01, expected_us)


def test_non_actant_prefix_mapping_to_dv01():
    calc = SpotRiskGreekCalculator()

    # Keys where the first two characters indicate the contract family
    zn_short = "ZNH5"
    us_short = "USU5"
    fv_short = "FVN5"
    tu_short = "TUN5"

    assert isclose(calc._get_futures_dv01(zn_short), DEFAULT_DV01)
    assert isclose(calc._get_futures_dv01(us_short), DEFAULT_DV01 / HEDGE_RATIOS["US"])
    assert isclose(calc._get_futures_dv01(fv_short), DEFAULT_DV01 / HEDGE_RATIOS["FV"])
    assert isclose(calc._get_futures_dv01(tu_short), DEFAULT_DV01 / HEDGE_RATIOS["TU"])


def test_unknown_series_falls_back_to_default():
    calc = SpotRiskGreekCalculator()
    # Unknown series should fall back to the calculator's default dv01
    unknown_key = "XCME.AB.SEP25"
    assert isclose(calc._get_futures_dv01(unknown_key), calc.dv01)


if __name__ == "__main__":
    # Simple runner to display DV01 calculations when executed directly
    calc = SpotRiskGreekCalculator()
    samples = [
        ("XCME.ZN.SEP25", "ZN", DEFAULT_DV01),
        ("XCME.ZF.SEP25", "FV", DEFAULT_DV01 / HEDGE_RATIOS["FV"]),
        ("XCME.ZT.SEP25", "TU", DEFAULT_DV01 / HEDGE_RATIOS["TU"]),
        ("XCME.ZB.SEP25", "US", DEFAULT_DV01 / HEDGE_RATIOS["US"]),
        ("XCME.AB.SEP25", "<fallback>", calc.dv01),
    ]
    for key, label, expected in samples:
        dv01 = calc._get_futures_dv01(key)
        print(f"{key} -> DV01: {dv01} (expected ~ {expected})")

