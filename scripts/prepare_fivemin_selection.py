from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
import re


def copy_days(src_root: Path, dst_root: Path, days: List[str]) -> None:
    dst_root.mkdir(parents=True, exist_ok=True)
    for d in days:
        src = src_root / d
        dst = dst_root / d
        if not src.exists():
            raise FileNotFoundError(f"Source folder not found: {src}")
        shutil.copytree(src, dst, dirs_exist_ok=True)


def read_expiries_from_csv(path: Path) -> Set[str]:
    expiries: Set[str] = set()
    try:
        with path.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            try:
                idx = header.index("expiry")
            except ValueError:
                return expiries
            for row in reader:
                if idx < len(row):
                    v = row[idx].strip()
                    if v:
                        expiries.add(v)
    except Exception:
        pass
    return expiries


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


def verify_required_expiries(root: Path, calendar_path: Path, requirements: Dict[str, List[str]]) -> Dict[str, object]:
    cal_map = load_calendar_map(calendar_path)
    report: Dict[str, object] = {"days": {}}

    for day, required_str_dates in requirements.items():
        day_dir = root / day
        required = {datetime.strptime(x, "%Y-%m-%d").date() for x in required_str_dates}
        files = sorted(day_dir.glob("*.csv"))
        files_status = []
        all_ok = True
        for f in files:
            tokens = read_expiries_from_csv(f)
            present_dates = {token_to_date_guess(t, cal_map) for t in tokens}
            present_dates = {d for d in present_dates if d is not None}
            missing = sorted({d.isoformat() for d in required if d not in present_dates})
            ok = len(missing) == 0
            if not ok:
                all_ok = False
            files_status.append({
                "file": str(f),
                "ok": ok,
                "missing_required": missing,
            })
        report["days"][day] = {
            "required": required_str_dates,
            "all_ok": all_ok,
            "files": files_status,
        }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Copy selected FiveMinuteMarket days and verify required expiries per file.")
    ap.add_argument("--src-root", default=r"C:\\Users\\ceterisparibus\\Documents\\ProductionSpace\\Hanyu\\FiveMinuteMarket")
    ap.add_argument("--dst-root", default="data/FiveMinuteMarketSelected")
    ap.add_argument("--days", nargs="+", default=["2025-08-19", "2025-08-20", "2025-08-21"])
    ap.add_argument("--calendar", default="ExpirationCalendar_CORRECTED_backup_20250720_150347.csv")
    ap.add_argument("--verify", action="store_true", help="Run verification after copy")
    args = ap.parse_args()

    src_root = Path(args.src_root)
    dst_root = Path(args.dst_root)

    copy_days(src_root, dst_root, args.days)

    if args.verify:
        requirements = {
            "2025-08-19": ["2025-08-19", "2025-08-20", "2025-08-21"],
            "2025-08-20": ["2025-08-20", "2025-08-21"],
            "2025-08-21": ["2025-08-21"],
        }
        report = verify_required_expiries(dst_root, Path(args.calendar), requirements)
        out_dir = dst_root / "verification"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "verification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        # Console summary
        for day, drep in report["days"].items():  # type: ignore
            print(day, "all_ok=", drep["all_ok"])  # type: ignore


if __name__ == "__main__":
    main()



