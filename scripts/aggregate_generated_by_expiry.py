#!/usr/bin/env python3
"""
Aggregate generated per-key CSVs into 10 files: Calls and Puts for each expiry
18AUG25, 19AUG25, 20AUG25, 21AUG25, and OZN_SEP25.

Inputs:
- Keys list: lib/trading/bond_future_options/data_validation/generated_actantrisk_keys_20250818_22.csv
- Per-key CSVs: lib/trading/bond_future_options/generatedcsvs/extracted_key_*.csv

Outputs:
- lib/trading/bond_future_options/generatedcsvs/aggregated/
  aggregated_18AUG25_C.csv
  aggregated_18AUG25_P.csv
  aggregated_19AUG25_C.csv
  aggregated_19AUG25_P.csv
  aggregated_20AUG25_C.csv
  aggregated_20AUG25_P.csv
  aggregated_21AUG25_C.csv
  aggregated_21AUG25_P.csv
  aggregated_OZN_SEP25_C.csv
  aggregated_OZN_SEP25_P.csv
"""

from __future__ import annotations

import os
import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
KEYS_CSV = REPO_ROOT / "lib/trading/bond_future_options/data_validation/generated_actantrisk_keys_20250818_22.csv"
GENERATED_DIR = REPO_ROOT / "lib/trading/bond_future_options/generatedcsvs"
OUTPUT_DIR = GENERATED_DIR / "aggregated"

# Mapping substrings in the key's base to expiry labels
EXPIRY_PATTERNS: Dict[str, str] = {
    ".VY3.18AUG25.": "18AUG25",
    ".GY3.19AUG25.": "19AUG25",
    ".WY3.20AUG25.": "20AUG25",
    ".HY3.21AUG25.": "21AUG25",
    ".OZN.SEP25.": "OZN_SEP25",
}


def sanitize_key_for_filename(key: str) -> str:
    return key.replace(".", "_").replace(":", "_").replace("/", "_")


def detect_timestamp_column(df: pd.DataFrame) -> str | None:
    candidates = [
        "timestamp",
        "market_time",
        "marketTradeTime",
        "time",
    ]
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_cols:
            return lower_cols[cand]
    return None


def load_keys() -> List[str]:
    keys: List[str] = []
    with open(KEYS_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return keys
        header = rows[0]
        if header and "key" in header:
            idx = header.index("key")
            data_rows = rows[1:]
            for r in data_rows:
                if r and len(r) > idx and r[idx].strip():
                    keys.append(r[idx].strip())
        else:
            for r in rows:
                if r and r[0].strip():
                    keys.append(r[0].strip())
    return keys


def group_keys_by_expiry_and_side(keys: List[str]) -> Dict[str, Dict[str, List[str]]]:
    groups: Dict[str, Dict[str, List[str]]] = {}
    for key in keys:
        expiry_label = None
        for pat, label in EXPIRY_PATTERNS.items():
            if pat in key:
                expiry_label = label
                break
        if expiry_label is None:
            continue
        # Side from last segment of key
        side = "C" if key.endswith(".C") else ("P" if key.endswith(".P") else None)
        if side is None:
            continue
        groups.setdefault(expiry_label, {}).setdefault(side, []).append(key)
    return groups


def aggregate_group(expiry_label: str, side: str, keys: List[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for key in keys:
        fname = GENERATED_DIR / f"extracted_key_{sanitize_key_for_filename(key)}.csv"
        if not fname.exists():
            # Skip keys that produced no rows
            continue
        try:
            df = pd.read_csv(fname)
            frames.append(df)
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    df_all = pd.concat(frames, ignore_index=True, sort=False)
    # Ensure strike exists as numeric for sorting
    if "strike" in df_all.columns:
        try:
            df_all["_strike_numeric"] = pd.to_numeric(df_all["strike"], errors="coerce")
        except Exception:
            df_all["_strike_numeric"] = pd.NA
    else:
        df_all["_strike_numeric"] = pd.NA
    # Detect timestamp
    ts_col = detect_timestamp_column(df_all)
    if ts_col is not None:
        try:
            df_all["_ts"] = pd.to_datetime(df_all[ts_col], errors="coerce")
        except Exception:
            df_all["_ts"] = pd.NaT
        df_all = df_all.sort_values(by=["_ts", "_strike_numeric"], ascending=[True, True], kind="mergesort")
    else:
        df_all = df_all.sort_values(by=["_strike_numeric"], ascending=[True], kind="mergesort")
    # Drop helper columns
    df_all = df_all.drop(columns=[c for c in ["_ts", "_strike_numeric"] if c in df_all.columns])
    return df_all


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    keys = load_keys()
    groups = group_keys_by_expiry_and_side(keys)
    targets = [
        ("18AUG25", "C"), ("18AUG25", "P"),
        ("19AUG25", "C"), ("19AUG25", "P"),
        ("20AUG25", "C"), ("20AUG25", "P"),
        ("21AUG25", "C"), ("21AUG25", "P"),
        ("OZN_SEP25", "C"), ("OZN_SEP25", "P"),
    ]
    for expiry_label, side in targets:
        key_list = groups.get(expiry_label, {}).get(side, [])
        df = aggregate_group(expiry_label, side, key_list)
        out_name = f"aggregated_{expiry_label}_{side}.csv"
        out_path = OUTPUT_DIR / out_name
        if df.empty:
            # Write an empty file with header for consistency if desired
            df.to_csv(out_path, index=False)
            print(f"Wrote empty aggregation: {out_path}")
        else:
            df.to_csv(out_path, index=False)
            print(f"Wrote {len(df)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




