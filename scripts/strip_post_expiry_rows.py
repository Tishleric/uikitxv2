from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, time
from pathlib import Path
from typing import Dict

# Map folder name like 19AUG25 to date
MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def parse_expiry_folder(name: str) -> datetime.date:
    dd = int(name[:2])
    mon = MONTHS[name[2:5]]
    yy = int(name[5:])
    year = 2000 + yy
    return datetime(year, mon, dd).date()


def strip_file_after_3pm_on(date_str: str, path: Path) -> Dict[str, int]:
    cutoff = time(15, 0, 0)
    removed = 0
    kept = 0
    tmp = path.with_suffix(path.suffix + ".tmp")
    with path.open("r", newline="", encoding="utf-8") as rfh, tmp.open("w", newline="", encoding="utf-8") as wfh:
        reader = csv.reader(rfh)
        writer = csv.writer(wfh)
        header = next(reader, [])
        writer.writerow(header)
        try:
            ts_idx = header.index("timestamp")
        except ValueError:
            # No timestamp column; copy as-is
            for row in reader:
                writer.writerow(row)
                kept += 1
            r = {"removed": removed, "kept": kept}
            path.unlink(); tmp.rename(path)
            return r
        for row in reader:
            ts_text = row[ts_idx]
            try:
                ts = datetime.strptime(ts_text, "%Y-%m-%d %H:%M:%S")
                if ts.date().isoformat() == date_str and ts.time() > cutoff:
                    removed += 1
                    continue
            except Exception:
                pass
            writer.writerow(row)
            kept += 1
    path.unlink(); tmp.rename(path)
    return {"removed": removed, "kept": kept}


def main() -> None:
    ap = argparse.ArgumentParser(description="Strip rows after 15:00 on the instrument's expiry date, in place")
    ap.add_argument("--root", default="data/FiveMinuteMarketSelected_by_instrument")
    args = ap.parse_args()

    root = Path(args.root)
    totals = {"files": 0, "removed": 0, "kept": 0}
    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir():
            continue
        expiry_date = parse_expiry_folder(exp_dir.name).isoformat()
        for f in sorted(exp_dir.glob("*.csv")):
            r = strip_file_after_3pm_on(expiry_date, f)
            totals["files"] += 1
            totals["removed"] += r["removed"]
            totals["kept"] += r["kept"]
    (root / "post_expiry_strip_summary.json").write_text(json.dumps(totals, indent=2), encoding="utf-8")
    print(totals)


if __name__ == "__main__":
    main()

