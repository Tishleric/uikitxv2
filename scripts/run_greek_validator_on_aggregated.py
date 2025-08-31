#!/usr/bin/env python3
"""
Runner: apply greek_validator_yaman.plot_pnl_diff to aggregated CSVs.

This does not modify greek_validator_yaman.py. It imports plot_pnl_diff and
invokes it with a dummy filename that encodes the expiry date so the
validator can locate ATM_C_<DATE>_vols.csv as designed.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

# Repo paths
REPO_ROOT = Path(__file__).resolve().parents[1]
AGG_DIR = REPO_ROOT / "lib/trading/bond_future_options/generatedcsvs/aggregated"
DATA_VALIDATION_DIR = REPO_ROOT / "lib/trading/bond_future_options/data_validation"

# Import validator
import sys as _sys
if str(REPO_ROOT / "lib" / "trading" / "bond_future_options") not in _sys.path:
    _sys.path.insert(0, str(REPO_ROOT / "lib" / "trading" / "bond_future_options"))

from greek_validator_yaman import plot_pnl_diff  # type: ignore


def expiry_from_filename(fname: str) -> str | None:
    # aggregated_<EXPIRY>_<SIDE>.csv
    name = Path(fname).name
    if not name.startswith("aggregated_") or not name.endswith(".csv"):
        return None
    core = name[len("aggregated_"):-len(".csv")]
    parts = core.split("_")
    if len(parts) < 2:
        return None
    # e.g., ["18AUG25", "C"] or ["OZN", "SEP25", "C"]
    if parts[0] == "OZN":
        return "22AUG25"  # Friday for OZN monthly per calendar (2025-08-22)
    return parts[0]


def main() -> int:
    files = sorted([p for p in AGG_DIR.glob("aggregated_*.csv") if p.is_file()])
    if not files:
        print(f"No aggregated files found in {AGG_DIR}")
        return 0

    for f in files:
        exp = expiry_from_filename(f.name)
        if not exp:
            print(f"Skip (cannot parse expiry): {f}")
            continue
        atm_path = DATA_VALIDATION_DIR / f"ATM_C_{exp}_vols.csv"
        if not atm_path.exists():
            print(f"Skip (missing ATM file): {atm_path}")
            continue
        try:
            df2 = pd.read_csv(f)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
            continue

        # Construct dummy filename so validator extracts correct date part
        dummy_filename = f"extracted_key_XCME_DUMMY_{exp}_D.csv"
        try:
            plot_pnl_diff(df2, dummy_filename)
            print(f"Processed {f.name} with expiry {exp}")
        except Exception as e:
            print(f"Validator failed on {f.name}: {e}")
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())




