#!/usr/bin/env python3
"""
Add a PricingMonkey column to ExpirationCalendar_CLEANED.csv.

PricingMonkey base key format (no strike/side): "<mon><yy> wkN <dow> ty"
Example: "sep25 wk1 thu ty".

Rules:
- N is the 1-based occurrence of that weekday in the month of the expiry date.
- Skip rows where Option Product contains "Future".
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
import pandas as pd


WEEKDAYS = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def compute_occurrence(dt: pd.Timestamp) -> int:
    target = dt.weekday()
    count = 0
    # Iterate days 1..dt.day within the month
    for day in range(1, dt.day + 1):
        d = pd.Timestamp(year=dt.year, month=dt.month, day=day)
        if d.weekday() == target:
            count += 1
    return count


def build_pm_base(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    dt = pd.to_datetime(date_str, errors="coerce")
    if pd.isna(dt):
        return None
    mon = dt.strftime("%b").lower()
    yy = dt.strftime("%y")
    dow = WEEKDAYS.get(dt.weekday(), "")
    occ = compute_occurrence(dt)
    return f"{mon}{yy} wk{occ} {dow} ty"


def main(path: Optional[str] = None) -> int:
    csv_path = Path(path) if path else Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
    df = pd.read_csv(csv_path)
    pm_values: list[str] = []
    for _, row in df.iterrows():
        prod = str(row.get("Option Product", ""))
        if "Future" in prod:
            pm_values.append("")
            continue
        pm = build_pm_base(str(row.get("Option Expiration Date (CT)", ""))) or ""
        pm_values.append(pm)
    df["PricingMonkey"] = pm_values
    df.to_csv(csv_path, index=False)
    print(f"Updated {csv_path} with PricingMonkey column (rows={len(df)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))


