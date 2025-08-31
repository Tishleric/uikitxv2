#!/usr/bin/env python3
"""
Generate ATM vols CSVs (ATM_{C|P}_{<DATE>}_vols.csv) from aggregated files by
calling atm_vols_yaman.vol(df2, expiry, type_of_option).

This script does not modify atm_vols_yaman.py.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import sys as _sys


REPO_ROOT = Path(__file__).resolve().parents[1]
AGG_DIR = REPO_ROOT / "lib/trading/bond_future_options/generatedcsvs/aggregated"

# Import atm_vols_yaman
ATM_MOD_DIR = REPO_ROOT / "lib/trading/bond_future_options"
if str(ATM_MOD_DIR) not in _sys.path:
    _sys.path.insert(0, str(ATM_MOD_DIR))

from atm_vols_yaman import vol  # type: ignore


def parse_expiry_and_side(name: str) -> tuple[str | None, str | None]:
    # Expect names like aggregated_18AUG25_C.csv or aggregated_OZN_SEP25_P.csv
    if not name.startswith("aggregated_") or not name.endswith(".csv"):
        return None, None
    core = name[len("aggregated_"):-len(".csv")]
    parts = core.split("_")
    if len(parts) < 2:
        return None, None
    side = parts[-1]
    if parts[0] == "OZN":
        # Friday mapping for OZN monthly
        expiry = "22AUG25"
    else:
        expiry = parts[0]
    return expiry, side


def main() -> int:
    files = sorted([p for p in AGG_DIR.glob("aggregated_*.csv") if p.is_file()])
    if not files:
        print(f"No aggregated files found in {AGG_DIR}")
        return 0
    for f in files:
        expiry, side = parse_expiry_and_side(f.name)
        if not expiry or side not in ("C", "P"):
            print(f"Skip (cannot parse): {f.name}")
            continue
        try:
            df2 = pd.read_csv(f)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
            continue
        try:
            vol(df2, expiry, side)
            print(f"Wrote ATM_{side}_{expiry}_vols.csv")
        except Exception as e:
            print(f"Failed vol() for {f.name}: {e}")
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




