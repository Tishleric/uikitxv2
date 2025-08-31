from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict


REMOVE = {
    "implied_vol",
    "delta_F",
    "delta_y",
    "gamma_F",
    "gamma_y",
    "speed_F",
    "speed_y",
    "theta_F",
    "vega_price",
    "vega_y",
    "calc_error",
}


def strip_file_in_place(path: Path) -> Dict[str, object]:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with path.open("r", newline="", encoding="utf-8") as rfh, tmp.open("w", newline="", encoding="utf-8") as wfh:
        reader = csv.reader(rfh)
        writer = csv.writer(wfh)
        header = next(reader)
        keep_idx = [i for i, h in enumerate(header) if h not in REMOVE]
        removed_cols = [h for h in header if h in REMOVE]
        new_header = [header[i] for i in keep_idx]
        writer.writerow(new_header)
        rows_before = 0
        rows_after = 0
        for row in reader:
            rows_before += 1
            writer.writerow([row[i] for i in keep_idx])
            rows_after += 1
    path.unlink()
    tmp.rename(path)
    return {
        "file": str(path),
        "removed_columns": removed_cols,
        "rows_before": rows_before,
        "rows_after": rows_after,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Strip specified columns from cleaned CSVs in place.")
    ap.add_argument("--root", default="data/FiveMinuteMarketSelected_clean")
    args = ap.parse_args()

    root = Path(args.root)
    report: Dict[str, object] = {"files": []}
    for day_dir in sorted(root.iterdir()):
        if not day_dir.is_dir():
            continue
        for path in sorted(day_dir.glob("*.csv")):
            report["files"].append(strip_file_in_place(path))

    (root / "final_strip_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Print one header line for sanity from first file per day
    for day_dir in sorted(root.iterdir()):
        if not day_dir.is_dir():
            continue
        sample = next(day_dir.glob("*.csv"), None)
        if sample:
            with sample.open("r", encoding="utf-8") as fh:
                line = fh.readline().strip()
                print(day_dir.name, "header:", line)


if __name__ == "__main__":
    main()



