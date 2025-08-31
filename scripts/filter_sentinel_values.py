from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

SENTINEL_STRINGS = {"-2146826259.0", "-2146826259", "-2.146826259E9", "-2.146826259e9"}
SENTINEL_VALUE = -2146826259.0
TARGET_COLS = {"bid", "ask", "adjtheor", "underlying_future_price"}


def filter_file_in_place(path: Path) -> Dict[str, object]:
    tmp = path.with_suffix(path.suffix + ".tmp")
    removed = 0
    kept = 0
    with path.open("r", newline="", encoding="utf-8") as rfh, tmp.open(
        "w", newline="", encoding="utf-8"
    ) as wfh:
        reader = csv.reader(rfh)
        writer = csv.writer(wfh)
        header = next(reader, [])
        writer.writerow(header)
        col_to_idx = {c: i for i, c in enumerate(header)}
        idxs = [col_to_idx[c] for c in TARGET_COLS if c in col_to_idx]
        for row in reader:
            def is_sentinel(val: str) -> bool:
                if val in SENTINEL_STRINGS:
                    return True
                try:
                    return float(val) == SENTINEL_VALUE
                except Exception:
                    return False

            if any((i < len(row) and is_sentinel(row[i])) for i in idxs):
                removed += 1
                continue
            writer.writerow(row)
            kept += 1
    path.unlink()
    tmp.rename(path)

    # Fallback: if sentinel still present anywhere in the file (e.g., unexpected column), drop any line containing it
    remaining = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if any(s in line for s in SENTINEL_STRINGS):
                remaining += 1
    if remaining:
        tmp2 = path.with_suffix(path.suffix + ".tmp2")
        with path.open("r", encoding="utf-8") as rfh, tmp2.open("w", encoding="utf-8") as wfh:
            for i, line in enumerate(rfh):
                if i == 0:  # header always keep
                    wfh.write(line)
                    continue
                if any(s in line for s in SENTINEL_STRINGS):
                    removed += 1
                    continue
                wfh.write(line)
        path.unlink()
        tmp2.rename(path)

    return {"file": str(path), "removed": removed, "kept": kept}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Drop rows with sentinel -2146826259.0 in bid/ask/adjtheor from per-instrument CSVs (in place)."
    )
    ap.add_argument("--root", default="data/FiveMinuteMarketSelected_by_instrument")
    args = ap.parse_args()

    root = Path(args.root)
    report: List[Dict[str, object]] = []
    for expiry_dir in sorted(root.iterdir()):
        if not expiry_dir.is_dir():
            continue
        removed_here = 0
        kept_here = 0
        for path in sorted(expiry_dir.glob("*.csv")):
            r = filter_file_in_place(path)
            report.append(r)
            removed_here += int(r["removed"])  # type: ignore
            kept_here += int(r["kept"])  # type: ignore
        print(expiry_dir.name, "removed:", removed_here, "kept:", kept_here)

    summary = {
        "total_files": len(report),
        "total_removed": sum(r["removed"] for r in report),
        "total_kept": sum(r["kept"] for r in report),
        "files": report,
    }
    (root / "sentinel_filter_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Files:", summary["total_files"], "Removed:", summary["total_removed"], "Kept:", summary["total_kept"]) 
