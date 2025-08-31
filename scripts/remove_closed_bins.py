from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List


FILENAME_RE = re.compile(r"five_min_market_(\d{8})_(\d{4})\.csv$")
DAY_DIR_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def list_day_dirs(root: Path, only_days: List[str] | None) -> List[Path]:
    if only_days:
        return [root / d for d in only_days]
    return [p for p in root.iterdir() if p.is_dir() and DAY_DIR_RE.search(p.name)]


def remove_hour_bins(root: Path, hour: int, days: List[str] | None = None, dry_run: bool = False) -> Dict[str, object]:
    report: Dict[str, object] = {"root": str(root), "hour": hour, "removed": [], "counts": {}, "errors": []}
    removed_list: List[str] = []
    counts: Dict[str, int] = {}

    for ddir in list_day_dirs(root, days):
        day = ddir.name
        c = 0
        for p in ddir.glob("*.csv"):
            m = FILENAME_RE.search(p.name)
            if not m:
                continue
            hm = m.group(2)
            hh = int(hm[:2])
            if hh == hour:
                try:
                    if not dry_run:
                        p.unlink()
                    removed_list.append(str(p))
                    c += 1
                except Exception as e:  # noqa: BLE001
                    report["errors"].append({"file": str(p), "error": str(e)})
        counts[day] = c

    report["removed"] = removed_list
    report["counts"] = counts
    report["total_removed"] = sum(counts.values())
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Remove closed-market 5-minute bins (e.g., 16:00-16:59) from selected day folders.")
    ap.add_argument("--root", default="data/FiveMinuteMarketSelected", help="Root folder containing day subfolders")
    ap.add_argument("--hour", type=int, default=16, help="Hour to remove (0-23). Default 16")
    ap.add_argument("--days", nargs="*", help="Optional explicit day folders like 2025-08-19 2025-08-20")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    report = remove_hour_bins(root, args.hour, args.days, args.dry_run)

    out_dir = root / "cleanup"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (out_dir / f"removed_{args.hour:02d}xx_{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Removed", report["total_removed"], f"files for hour {args.hour:02d}")
    for day, cnt in report["counts"].items():
        print(day, cnt)


if __name__ == "__main__":
    main()



