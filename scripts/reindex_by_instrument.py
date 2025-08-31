from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def discover_header(root: Path) -> List[str]:
    for day_dir in sorted(root.iterdir()):
        if not day_dir.is_dir():
            continue
        for p in sorted(day_dir.glob("*.csv")):
            with p.open("r", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader, [])
                if header:
                    return header
    raise RuntimeError("No CSV files found to discover header")


def sanitize_strike(s: str) -> str:
    return s.replace(":", "_").replace(".", "_")


def main() -> None:
    ap = argparse.ArgumentParser(description="Reindex cleaned snapshots into per-instrument time series.")
    ap.add_argument("--src", default="data/FiveMinuteMarketSelected_clean")
    ap.add_argument("--dst", default="data/FiveMinuteMarketSelected_by_instrument")
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    header = discover_header(src)
    # Required columns
    col_to_idx = {c: i for i, c in enumerate(header)}
    for required in ["timestamp", "expiry", "strike", "itype"]:
        if required not in col_to_idx:
            raise RuntimeError(f"Missing required column '{required}' in source files")

    series: Dict[Tuple[str, str, str], List[List[str]]] = defaultdict(list)
    source_days: Dict[Tuple[str, str, str], set] = defaultdict(set)

    for day_dir in sorted(src.iterdir()):
        if not day_dir.is_dir():
            continue
        day = day_dir.name
        for p in sorted(day_dir.glob("*.csv")):
            with p.open("r", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                h = next(reader, [])
                if h != header:
                    # Align columns if order differs: build a row reordered to match master header
                    idx_map = [h.index(c) for c in header]
                else:
                    idx_map = list(range(len(header)))
                for row in reader:
                    # Reorder row to master header
                    row2 = [row[i] if i < len(row) else "" for i in idx_map]
                    expiry = row2[col_to_idx["expiry"]].strip()
                    strike = row2[col_to_idx["strike"]].strip()
                    itype = row2[col_to_idx["itype"]].strip()
                    key = (expiry, strike, itype)
                    series[key].append(row2)
                    source_days[key].add(day)

    # Write per-instrument files
    index_rows: List[Dict[str, object]] = []
    for (expiry, strike, itype), rows in series.items():
        # sort by timestamp
        ts_idx = col_to_idx["timestamp"]
        rows.sort(key=lambda r: r[ts_idx])
        # dedupe exact timestamps (keep last)
        dedup: Dict[str, List[str]] = {}
        for r in rows:
            dedup[r[ts_idx]] = r
        rows_sorted = [dedup[k] for k in sorted(dedup.keys())]

        subdir = dst / expiry
        subdir.mkdir(parents=True, exist_ok=True)
        fname = f"{expiry}_{sanitize_strike(strike)}_{itype}.csv"
        out = subdir / fname
        with out.open("w", newline="", encoding="utf-8") as wfh:
            writer = csv.writer(wfh)
            writer.writerow(header)
            writer.writerows(rows_sorted)

        index_rows.append({
            "expiry": expiry,
            "strike": strike,
            "itype": itype,
            "rows": len(rows_sorted),
            "first_ts": rows_sorted[0][ts_idx] if rows_sorted else None,
            "last_ts": rows_sorted[-1][ts_idx] if rows_sorted else None,
            "source_days": sorted(list(source_days[(expiry, strike, itype)])),
            "path": str(out),
        })

    # Write index files
    (dst / "instrument_index.json").write_text(json.dumps(index_rows, indent=2), encoding="utf-8")
    with (dst / "instrument_index.csv").open("w", newline="", encoding="utf-8") as wfh:
        writer = csv.writer(wfh)
        writer.writerow(["expiry", "strike", "itype", "rows", "first_ts", "last_ts", "source_days", "path"])
        for r in index_rows:
            writer.writerow([
                r["expiry"], r["strike"], r["itype"], r["rows"], r["first_ts"], r["last_ts"], "|".join(r["source_days"]), r["path"],
            ])

    print("Instruments:", len(index_rows))
    print("Output root:", dst)


if __name__ == "__main__":
    main()



