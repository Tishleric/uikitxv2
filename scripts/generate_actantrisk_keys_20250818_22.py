#!/usr/bin/env python3
"""
Generate ActantRisk option keys for 2025-08-18 .. 2025-08-22 inclusive,
with quarter-step strikes 110.00 .. 114.75 for both calls and puts.

Sources:
- data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv
- Strike formatting: lib/trading/market_prices/strike_converter.py

Output:
- Writes CSV at data/output/integration_test/generated_actantrisk_keys_20250818_22.csv
  with one column 'key'.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Set

import pandas as pd

# Ensure repo root is importable when running from scripts/
REPO_ROOT = Path(__file__).resolve().parents[1]
import sys as _sys
if str(REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(REPO_ROOT))

# Local imports (after path setup)
from lib.trading.market_prices.strike_converter import StrikeConverter


CSV_PATH = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
OUTPUT_PATH = Path("lib/trading/bond_future_options/data_validation/generated_actantrisk_keys_20250818_22.csv")


def _parse_ct_date(dt_str: str) -> date:
    # Calendar has formats like "8/18/2025 14:00" for options, or just dates for futures
    dt_str = str(dt_str).strip()
    # Try datetime with time first
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(dt_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {dt_str}")


def _build_strike_list(min_strike: float, max_strike: float, step: float) -> List[float]:
    strikes: List[float] = []
    val = min_strike
    # Guard against floating errors by stepping in integers
    n_steps = int(round((max_strike - min_strike) / step))
    for i in range(n_steps + 1):
        strikes.append(round(min_strike + i * step, 2))
    return strikes


def _format_strike_actantrisk(k: float) -> str:
    return StrikeConverter.format_strike(k, "actantrisk")


def _load_calendar() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Calendar CSV not found: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    return df


def _filter_expiry_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    # Parse once
    df = df.copy()
    df["expiry_date"] = df["Option Expiration Date (CT)"].apply(_parse_ct_date)
    mask = (df["expiry_date"] >= start) & (df["expiry_date"] <= end)
    # Only include options rows (skip futures bases without options)
    return df.loc[mask].reset_index(drop=True)


def _extract_actantrisk_bases(df: pd.DataFrame) -> Set[str]:
    bases: Set[str] = set()
    for _, row in df.iterrows():
        base = str(row.get("ActantRisk", "")).strip()
        if base:
            bases.add(base)
    return bases


def _generate_keys_for_bases(bases: Set[str], strikes: List[float]) -> Set[str]:
    keys: Set[str] = set()
    for base in sorted(bases):
        # Expect base like XCME.WY3.20AUG25 or XCME.OZN.SEP25
        for k in strikes:
            k_str = _format_strike_actantrisk(k)
            keys.add(f"{base}.{k_str}.C")
            keys.add(f"{base}.{k_str}.P")
    return keys


def main() -> int:
    start = date(2025, 8, 18)
    end = date(2025, 8, 22)
    strikes = _build_strike_list(110.0, 114.0, 0.25)

    df = _load_calendar()
    df_range = _filter_expiry_range(df, start, end)

    # Include Friday OZN monthly as it appears on 2025-08-22
    # The filter already captures all rows in the range, including OZN friday rows.
    bases = _extract_actantrisk_bases(df_range)

    keys = _generate_keys_for_bases(bases, strikes)

    # Ensure output directory
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(sorted(keys), columns=["key"])
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Generated {len(keys)} keys. Written to {OUTPUT_PATH}")
    # Show a few samples
    for s in list(sorted(keys))[:5]:
        print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())


