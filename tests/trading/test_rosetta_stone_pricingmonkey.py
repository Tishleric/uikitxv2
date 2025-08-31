from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
import pytest


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lib.trading.market_prices.rosetta_stone import RosettaStone  # type: ignore


def _load_sample_rows(limit: int = 8) -> List[Dict[str, str]]:
    csv_path = ROOT / "data" / "reference" / "symbol_translation" / "ExpirationCalendar_CLEANED.csv"
    df = pd.read_csv(csv_path)
    mask = (
        ~df["Option Product"].astype(str).str.contains("Future", na=False)
        & df["Bloomberg_Call"].notna()
        & df["Bloomberg_Put"].notna()
        & df.get("PricingMonkey").notna()
        & (df.get("PricingMonkey") != "")
    )
    rows = df[mask].head(limit)
    out: List[Dict[str, str]] = []
    for _, r in rows.iterrows():
        out.append(
            {
                "bb_call": str(r["Bloomberg_Call"]),
                "bb_put": str(r["Bloomberg_Put"]),
                "pm_base": str(r["PricingMonkey"]).strip(),
                "actant_trades": str(r.get("ActantTrades", "")) if "ActantTrades" in r else "",
            }
        )
    return out


CASES = _load_sample_rows()


@pytest.mark.parametrize(
    "bb_base, side, pm_base",
    [(c["bb_call"], "C", c["pm_base"]) for c in CASES]
    + [(c["bb_put"], "P", c["pm_base"]) for c in CASES],
)
def test_bloomberg_to_pricingmonkey_roundtrip(bb_base: str, side: str, pm_base: str) -> None:
    rs = RosettaStone()
    strike = "112.50"
    pm_full = rs.translate(f"{bb_base} {strike} Comdty", "bloomberg", "pricingmonkey")
    assert pm_full is not None
    expected_pm = f"{pm_base} {strike} {'call' if side == 'C' else 'put'}"
    assert pm_full == expected_pm

    bb_full2 = rs.translate(pm_full, "pricingmonkey", "bloomberg")
    # Bloomberg formatting may drop trailing zero; accept either form
    assert bb_full2 in (f"{bb_base} {strike} Comdty", f"{bb_base} {float(strike):g} Comdty")


@pytest.mark.parametrize(
    "bb_base",
    [c["bb_call"] for c in CASES] + [c["bb_put"] for c in CASES],
)
def test_bloomberg_to_cme_and_back(bb_base: str) -> None:
    rs = RosettaStone()
    strike = "112.50"
    cme = rs.translate(f"{bb_base} {strike} Comdty", "bloomberg", "cme")
    assert cme is not None
    bb_full2 = rs.translate(cme, "cme", "bloomberg")
    assert bb_full2 in (f"{bb_base} {strike} Comdty", f"{bb_base} {float(strike):g} Comdty")


@pytest.mark.parametrize(
    "bb_base",
    [c["bb_call"] for c in CASES] + [c["bb_put"] for c in CASES],
)
def test_bloomberg_to_actantrisk_and_back(bb_base: str) -> None:
    rs = RosettaStone()
    strike = "112.50"
    ar = rs.translate(f"{bb_base} {strike} Comdty", "bloomberg", "actantrisk")
    assert ar is not None
    bb_full2 = rs.translate(ar, "actantrisk", "bloomberg")
    assert bb_full2 == f"{bb_base} {strike} Comdty"


@pytest.mark.parametrize("row", CASES)
def test_actanttrades_to_bloomberg_when_available(row: Dict[str, str]) -> None:
    at = row.get("actant_trades", "")
    if not at or at == "nan":
        pytest.skip("No ActantTrades base available in row")
    rs = RosettaStone()
    bb = rs.translate(at, "actanttrades", "bloomberg")
    # If mapping exists, it should resolve to either the call or put base
    if bb is None:
        # Option bases without strike should fail; futures may pass
        # Accept None for options; skip only if mapping absent entirely
        return
    assert any(bb.startswith(b) for b in (row["bb_call"], row["bb_put"]))


