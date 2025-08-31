from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


FILENAME_RE = re.compile(r"five_min_market_(\d{8})_(\d{4})\.csv$")


def load_calendar_map(calendar_path: Path) -> Dict[str, date]:
    token_to_date: Dict[str, date] = {}
    if not calendar_path.exists():
        return token_to_date
    with calendar_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            x = row.get("XCME", "")
            m = re.search(r"\.([A-Z]{3}\d{2})\.", x)
            if not m:
                continue
            tok = m.group(1)
            dt_str = row.get("Option Expiration Date (CT)", "").split(" ")[0]
            try:
                d = datetime.strptime(dt_str, "%m/%d/%Y").date()
            except Exception:
                continue
            token_to_date[tok] = d
    return token_to_date


def token_to_date_guess(tok: str, cal_map: Dict[str, date]) -> Optional[date]:
    if tok in cal_map:
        return cal_map[tok]
    m = re.fullmatch(r"(\d{1,2})([A-Z]{3})(\d{2,4})", tok)
    if m:
        dd, mon, yy = m.groups()
        year = int(yy)
        if year < 100:
            year += 2000
        try:
            return datetime.strptime(f"{dd}{mon}{year}", "%d%b%Y").date()
        except ValueError:
            return None
    m2 = re.fullmatch(r"([A-Z]{3})(\d{2,4})", tok)
    if m2:
        return cal_map.get(tok)
    return None


def filter_csv_by_expiry(src: Path, dst: Path, allowed_dates: Set[date], cal_map: Dict[str, date]) -> Dict[str, object]:
    rows_before = 0
    rows_after = 0
    kept_tokens: Set[str] = set()
    dropped_tokens: Set[str] = set()

    with src.open("r", newline="", encoding="utf-8") as rfh, dst.open("w", newline="", encoding="utf-8") as wfh:
        reader = csv.reader(rfh)
        writer = csv.writer(wfh)
        header = next(reader)
        writer.writerow(header)
        try:
            idx = header.index("expiry")
        except ValueError:
            # no expiry column; copy nothing
            return {"file": str(src), "rows_before": 0, "rows_after": 0, "kept": [], "dropped": []}
        for row in reader:
            rows_before += 1
            tok = row[idx].strip() if idx < len(row) else ""
            dt = token_to_date_guess(tok, cal_map)
            if dt is not None and dt in allowed_dates:
                writer.writerow(row)
                rows_after += 1
                kept_tokens.add(tok)
            else:
                if tok:
                    dropped_tokens.add(tok)

    return {
        "file": str(src),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "kept": sorted(kept_tokens),
        "dropped": sorted(dropped_tokens),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Filter FiveMinuteMarketSelected to keep only allowed expiries per day.")
    ap.add_argument("--src", default="data/FiveMinuteMarketSelected")
    ap.add_argument("--dst", default="data/FiveMinuteMarketSelected_clean")
    ap.add_argument("--calendar", default="ExpirationCalendar_CORRECTED_backup_20250720_150347.csv")
    args = ap.parse_args()

    cal_map = load_calendar_map(Path(args.calendar))
    src = Path(args.src)
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    allow: Dict[str, Set[date]] = {
        "2025-08-19": {datetime(2025, 8, 19).date(), datetime(2025, 8, 20).date(), datetime(2025, 8, 21).date()},
        "2025-08-20": {datetime(2025, 8, 20).date(), datetime(2025, 8, 21).date()},
        "2025-08-21": {datetime(2025, 8, 21).date()},
    }

    report: Dict[str, object] = {"days": {}}
    for day, allowed in allow.items():
        day_src = src / day
        day_dst = dst / day
        day_dst.mkdir(parents=True, exist_ok=True)
        files = sorted(day_src.glob("*.csv"))
        file_reports: List[Dict[str, object]] = []
        for f in files:
            out = day_dst / f.name
            file_reports.append(filter_csv_by_expiry(f, out, allowed, cal_map))
        report["days"][day] = file_reports

    (dst / "clean_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Console summary
    for day, reps in report["days"].items():  # type: ignore
        kept: Set[str] = set()
        for r in reps:  # type: ignore
            kept.update(r["kept"])  # type: ignore
        print(day, "kept tokens:", ", ".join(sorted(kept)))


if __name__ == "__main__":
    main()



