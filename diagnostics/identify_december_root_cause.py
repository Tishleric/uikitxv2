"""
Diagnostic script to identify why December futures were treated as non-FUTURE.

This script:
- Parses the provided debug CSV chunks under data/reference/market data debug/
- Uses existing parser (no code changes) to build DataFrames
- Verifies RosettaStone translation for each row
- Detects any rows whose bloomberg_symbol equals a pure futures symbol while not being a FUTURE
- Simulates the aggregator dedup (drop_duplicates keep='last') and reports the survivor instrument_type

Run:
  python diagnostics/identify_december_root_cause.py | more
"""

from __future__ import annotations

import os
import glob
import pandas as pd

# Import existing modules (no edits to them)
# Ensure project root is on sys.path so `lib.*` imports resolve when run directly
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.market_prices.rosetta_stone import RosettaStone


def map_itype_to_instrument_type(val: str | None) -> str:
    if val is None:
        return 'UNKNOWN'
    s = str(val).upper().strip()
    if s in {'F', 'FUTURE'}:
        return 'FUTURE'
    if s in {'C', 'CALL'}:
        return 'CALL'
    if s in {'P', 'PUT'}:
        return 'PUT'
    return s or 'UNKNOWN'


def main() -> None:
    base_dir = os.path.join('data', 'reference', 'market data debug')
    paths = sorted(glob.glob(os.path.join(base_dir, 'bav_analysis_*_chunk_*_of_*.csv')))
    if not paths:
        print(f"No debug CSVs found in: {base_dir}")
        return

    translator = RosettaStone()
    frames: list[pd.DataFrame] = []

    print("=== Parsing CSV chunks and verifying translator outputs ===")
    for p in paths:
        try:
            df = parse_spot_risk_csv(p, calculate_time_to_expiry=False, vtexp_data=None)
        except Exception as e:
            print(f"ERROR parsing {os.path.basename(p)}: {e}")
            continue

        # Normalize expected columns
        if 'key' not in df.columns:
            print(f"WARN: no 'key' column in {os.path.basename(p)}; columns={list(df.columns)}")
            continue

        # Ensure bloomberg_symbol via translator (parser already sets it, but recompute for certainty)
        df['bb_from_translator'] = df['key'].apply(lambda x: translator.translate(x, 'actantrisk', 'bloomberg') if pd.notna(x) else None)
        if 'bloomberg_symbol' not in df.columns:
            df['bloomberg_symbol'] = df['bb_from_translator']

        # Instrument type
        itype_col = 'itype' if 'itype' in df.columns else None
        df['instrument_type_sim'] = df[itype_col].apply(map_itype_to_instrument_type) if itype_col else 'UNKNOWN'

        frames.append(df)

    if not frames:
        print("No data frames parsed; aborting.")
        return

    full = pd.concat(frames, ignore_index=True)

    # Identify pure futures symbols present in data (from rows with FUTURE itype)
    futures_rows = full[full['instrument_type_sim'] == 'FUTURE'].copy()
    futures_symbols: set[str] = set(
        futures_rows['bb_from_translator']
        .dropna()
        .astype(str)
        .tolist()
    )
    futures_symbols = {s for s in futures_symbols if s.endswith(' Comdty')}

    print("\n=== Futures Bloomberg symbols detected in this dataset ===")
    for s in sorted(futures_symbols):
        print(f"  - {s}")

    # Find any collision: non-FUTURE rows that map to a pure futures symbol
    suspects = full[(full['instrument_type_sim'] != 'FUTURE') & (full['bb_from_translator'].isin(futures_symbols))]
    print("\n=== Collisions (non-FUTURE rows mapping to a pure futures symbol) ===")
    if suspects.empty:
        print("  None found in this dataset.")
    else:
        cols = ['key', 'itype', 'instrument_type_sim', 'bb_from_translator', 'bloomberg_symbol', 'midpoint_price']
        print(suspects[cols].head(20).to_string(index=False))
        print(f"\nTotal collisions found: {len(suspects)}")

    # Simulate aggregator dedup: keep last per bloomberg_symbol
    # Use the parser-provided bloomberg_symbol to mirror aggregator (it recomputes, but should match)
    # Drop rows with missing bloomberg_symbol like aggregator does
    agg_like = full.dropna(subset=['bloomberg_symbol']).copy()
    agg_like = agg_like.reset_index(drop=True)
    survivors = agg_like.drop_duplicates(subset=['bloomberg_symbol'], keep='last')

    # Report survivor instrument type for each futures symbol present
    print("\n=== Aggregator-like survivors for futures symbols (keep-last policy) ===")
    report_rows = []
    for sym in sorted(futures_symbols):
        row = survivors[survivors['bloomberg_symbol'] == sym]
        if row.empty:
            status = 'MISSING (no survivor)'
        else:
            itype = row['itype'].iloc[0] if 'itype' in row.columns else None
            itype_sim = map_itype_to_instrument_type(itype)
            status = f"survivor_type={itype_sim} (itype={itype})"
        report_rows.append((sym, status))

    for sym, status in report_rows:
        print(f"  - {sym}: {status}")

    # If any survivor for a futures symbol is not FUTURE -> likely cause is dedup overshadowing
    bad = [sym for sym, status in report_rows if 'survivor_type=FUTURE' not in status]
    if bad:
        print("\n=== Likely root cause: dedup overshadowed FUTURE for these symbols ===")
        for sym in bad:
            print(f"  * {sym}")
            # Show the last few rows contributing to this symbol in the concatenated data
            subset = agg_like[agg_like['bloomberg_symbol'] == sym]
            cols = ['key', 'itype', 'instrument_type_sim', 'bloomberg_symbol', 'price_source']
            cols = [c for c in cols if c in subset.columns]
            print(subset[cols].tail(5).to_string(index=False))
    else:
        print("\nNo FUTURE survivor was overshadowed in the keep-last simulation.")

    # --- Additional DEC25 option translation sampling and counts ---
    print("\n=== DEC25 option translation samples (TY*, US*, ZT*) ===")
    is_dec25 = full['key'].astype(str).str.contains('.DEC25', regex=False)
    is_option = full['instrument_type_sim'].isin(['CALL', 'PUT'])
    dec_opts = full[is_dec25 & is_option].copy()

    # Focus output to common Treasury roots
    mask_roots = (
        dec_opts['key'].astype(str).str.contains('.ZN.', regex=False) |
        dec_opts['key'].astype(str).str.contains('.ZB.', regex=False) |
        dec_opts['key'].astype(str).str.contains('.ZT.', regex=False)
    )
    dec_opts_roots = dec_opts[mask_roots]

    sample_cols = ['key', 'itype', 'bb_from_translator']
    if not dec_opts_roots.empty:
        print(dec_opts_roots[sample_cols].head(15).to_string(index=False))
    else:
        print("  No DEC25 options for ZN/ZB/ZT roots in this sample.")

    # Per-futures-symbol counts of FUTURE vs OPTION rows (pre-dedup)
    print("\n=== Counts per futures symbol (FUTURE vs OPTION) before dedup ===")
    for sym in sorted(futures_symbols):
        sub = full[full['bb_from_translator'] == sym]
        f_cnt = int((sub['instrument_type_sim'] == 'FUTURE').sum())
        o_cnt = int((sub['instrument_type_sim'].isin(['CALL', 'PUT'])).sum())
        print(f"  - {sym}: FUTURE={f_cnt}, OPTIONS={o_cnt}")


if __name__ == '__main__':
    main()


