from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time, date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    _zoneinfo_ok = True
except Exception:  # pragma: no cover
    try:
        from backports.zoneinfo import ZoneInfo  # type: ignore
        _zoneinfo_ok = True
    except Exception:
        ZoneInfo = None  # type: ignore
        _zoneinfo_ok = False


CT_TZ = ZoneInfo("America/Chicago") if _zoneinfo_ok else None
FILENAME_RE = re.compile(r"five_min_market_(\d{8})_(\d{4})\.csv$")


@dataclass
class DayCoverage:
    trading_day: date
    phase_minute: int
    expected_count: int
    present_count: int
    coverage: float
    largest_gap_min: int
    files_by_bin: Dict[str, str]


def parse_filename_ts(path: Path) -> Optional[datetime]:
    """Parse CT timestamp from filename like five_min_market_YYYYMMDD_HHMM.csv.

    Returns timezone-aware datetime in America/Chicago on success, else None.
    """
    m = FILENAME_RE.search(path.name)
    if not m:
        return None
    ymd, hm = m.groups()
    dt = datetime.strptime(f"{ymd}{hm}", "%Y%m%d%H%M")
    return dt.replace(tzinfo=CT_TZ) if CT_TZ is not None else dt


def trading_day_for(ts_ct: datetime) -> date:
    """Map a wall-clock CT timestamp to its trading day date.

    Trading day runs from 17:00 (5pm) previous calendar day to 16:00 (4pm) current day.
    """
    cutoff = time(17, 0, tzinfo=CT_TZ) if CT_TZ is not None else time(17, 0)
    cur_t = ts_ct.timetz() if CT_TZ is not None else ts_ct.time()
    if cur_t >= cutoff:
        return (ts_ct + timedelta(days=1)).date()
    return ts_ct.date()


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("five_min_market_*.csv"):
        if FILENAME_RE.search(p.name):
            yield p


def build_bins(start: datetime, end: datetime, phase_minute: int) -> List[datetime]:
    """Build 5-min bins [start, end) aligned to phase_minute = minute % 5.
    Returns a list of timezone-aware datetimes.
    """
    # advance to first time >= start with minute%5 == phase
    cur = start
    if cur.minute % 5 != phase_minute:
        delta_min = (phase_minute - (cur.minute % 5)) % 5
        cur += timedelta(minutes=delta_min)
    bins: List[datetime] = []
    while cur < end:
        bins.append(cur)
        cur += timedelta(minutes=5)
    return bins


def compute_daily_coverage(files: List[Path]) -> Dict[date, DayCoverage]:
    by_day: Dict[date, Dict[str, str]] = {}
    by_day_first_minute: Dict[date, int] = {}

    for f in files:
        ts = parse_filename_ts(f)
        if ts is None:
            continue
        td = trading_day_for(ts)
        key = ts.strftime("%Y-%m-%d %H:%M")
        by_day.setdefault(td, {})[key] = str(f)
        by_day_first_minute.setdefault(td, ts.minute)

    day_cov: Dict[date, DayCoverage] = {}
    for td, files_by_bin in sorted(by_day.items()):
        phase = by_day_first_minute[td] % 5
        if CT_TZ is not None:
            session_start = datetime.combine(td - timedelta(days=1), time(17, 0), CT_TZ)
            session_end = datetime.combine(td, time(16, 0), CT_TZ)
        else:
            session_start = datetime.combine(td - timedelta(days=1), time(17, 0))
            session_end = datetime.combine(td, time(16, 0))
        expected_bins = build_bins(session_start, session_end, phase)
        expected_keys = {b.strftime("%Y-%m-%d %H:%M") for b in expected_bins}

        present = set(files_by_bin.keys()) & expected_keys
        present_count = len(present)
        expected_count = len(expected_keys)
        coverage = present_count / expected_count if expected_count else 0.0

        # largest consecutive missing gap (in minutes)
        largest_gap = 0
        cur_gap = 0
        for b in expected_bins:
            if b.strftime("%Y-%m-%d %H:%M") in present:
                largest_gap = max(largest_gap, cur_gap)
                cur_gap = 0
            else:
                cur_gap += 5
        largest_gap = max(largest_gap, cur_gap)

        day_cov[td] = DayCoverage(
            trading_day=td,
            phase_minute=phase,
            expected_count=expected_count,
            present_count=present_count,
            coverage=coverage,
            largest_gap_min=largest_gap,
            files_by_bin=files_by_bin,
        )
    return day_cov


def expected_bins_for_day(c: DayCoverage) -> Tuple[List[datetime], Set[str]]:
    """Regenerate expected 5-minute bins and their formatted keys for a day.
    Session: prior 17:00 → current 16:00 CT, aligned to phase_minute.
    """
    td = c.trading_day
    if CT_TZ is not None:
        start = datetime.combine(td - timedelta(days=1), time(17, 0), CT_TZ)
        end = datetime.combine(td, time(16, 0), CT_TZ)
    else:
        start = datetime.combine(td - timedelta(days=1), time(17, 0))
        end = datetime.combine(td, time(16, 0))
    bins = build_bins(start, end, c.phase_minute)
    keys = {b.strftime("%Y-%m-%d %H:%M") for b in bins}
    return bins, keys


def missing_intervals_for_day(c: DayCoverage) -> List[Dict[str, object]]:
    """Return contiguous missing intervals as [{start,end,minutes}]."""
    bins, keys = expected_bins_for_day(c)
    present = set(c.files_by_bin.keys()) & keys
    intervals: List[Dict[str, object]] = []
    run_start: Optional[datetime] = None
    run_len = 0
    for b in bins:
        if b.strftime("%Y-%m-%d %H:%M") in present:
            if run_start is not None:
                intervals.append({
                    "start": run_start.strftime("%Y-%m-%d %H:%M"),
                    "end": b.strftime("%Y-%m-%d %H:%M"),
                    "minutes": run_len,
                })
                run_start = None
                run_len = 0
        else:
            if run_start is None:
                run_start = b
                run_len = 0
            run_len += 5
    if run_start is not None:
        intervals.append({
            "start": run_start.strftime("%Y-%m-%d %H:%M"),
            "end": (bins[-1] + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M"),
            "minutes": run_len,
        })
    return intervals

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
                    val = row[idx].strip()
                    if val:
                        expiries.add(val)
    except Exception:
        pass
    return expiries


def load_expiration_calendar_map(calendar_path: Optional[Path]) -> Dict[str, date]:
    """Load mapping like 'SEP25' -> 2025-08-22 from calendar CSV if available."""
    token_to_date: Dict[str, date] = {}
    if not calendar_path or not calendar_path.exists():
        return token_to_date
    with calendar_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            token = row.get("CME", "")
            # e.g., OZNQ5 C011100 not helpful; use XCME field like XCME.OZN.SEP25.11.C
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
    if m2 and m2.group(1) in {
        "JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"
    }:
        return cal_map.get(tok)
    return None


def collect_day_expiries(cov: DayCoverage) -> Dict[str, Set[str]]:
    """Return mapping bin_key -> set(expiry tokens) for the day."""
    result: Dict[str, Set[str]] = {}
    for bin_key, p in cov.files_by_bin.items():
        expiries = read_expiries_from_csv(Path(p))
        result[bin_key] = expiries
    return result


def find_best_windows(
    days: Dict[date, DayCoverage],
    min_coverage: float,
) -> List[List[date]]:
    ordered_days = sorted(days.keys())
    windows: List[List[date]] = []
    # build consecutive weekday sequences of length 5
    for i in range(len(ordered_days) - 4):
        seq = ordered_days[i : i + 5]
        ok = True
        cur = seq[0]
        for nxt in seq[1:]:
            # next business day (skip weekends)
            d = cur + timedelta(days=1)
            while d.weekday() >= 5:
                d += timedelta(days=1)
            if d != nxt:
                ok = False
                break
            cur = nxt
        if not ok:
            continue
        if all(days[d].coverage >= min_coverage for d in seq):
            windows.append(seq)
    return windows


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan FiveMinuteMarket for 5-day windows with good coverage and expiry progression.")
    ap.add_argument("--root", default=r"C:\\Users\\ceterisparibus\\Documents\\ProductionSpace\\Hanyu\\FiveMinuteMarket", help="Root directory to scan")
    ap.add_argument("--calendar", default="ExpirationCalendar_CORRECTED_backup_20250720_150347.csv", help="Expiration calendar CSV to map monthly tokens (optional)")
    ap.add_argument("--min-coverage", type=float, default=0.90, help="Minimum per-day coverage threshold (0-1)")
    ap.add_argument("--out", default="reports/fivemin_market_search", help="Output directory for reports")
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out) / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(iter_files(root))
    daily = compute_daily_coverage(files)

    # write per-day coverage json
    cov_json = {
        d.isoformat(): (lambda _d: (_d.__setitem__("trading_day", c.trading_day.isoformat()) or _d))(asdict(c))
        for d, c in daily.items()
    }
    (out_dir / "coverage_by_day.json").write_text(json.dumps(cov_json, indent=2))

    # Build all rolling 5-business-day windows (no filtering) for ranking & visuals
    ordered_days = sorted(daily.keys())
    all_windows: List[List[date]] = []
    for i in range(len(ordered_days) - 4):
        seq = ordered_days[i : i + 5]
        ok = True
        cur = seq[0]
        for nxt in seq[1:]:
            d = cur + timedelta(days=1)
            while d.weekday() >= 5:
                d += timedelta(days=1)
            if d != nxt:
                ok = False
                break
            cur = nxt
        if ok:
            all_windows.append(seq)

    # Windows that pass the min-coverage filter (legacy candidates)
    windows = [w for w in all_windows if all(daily[d].coverage >= args.min_coverage for d in w)]
    candidates: List[Dict[str, object]] = []

    cal_map = load_expiration_calendar_map(Path(args.calendar))

    for seq in windows:
        per_day = []
        for d in seq:
            cov = daily[d]
            bin_to_exp = collect_day_expiries(cov)
            # union of expiries for the day
            day_tokens: Set[str] = set().union(*bin_to_exp.values()) if bin_to_exp else set()
            # derive required expiries set: remaining trading days in window
            required_dates = [x for x in seq if x >= d]
            required_tokens: Set[str] = set()
            for rd in required_dates:
                # accept any token mapping to rd
                required_tokens.add(rd.isoformat())
            token_to_date_map: Dict[str, Optional[date]] = {
                t: token_to_date_guess(t, cal_map) for t in day_tokens
            }
            present_required = {
                rd.isoformat()
                for t, dt_ in token_to_date_map.items()
                for rd in required_dates
                if dt_ == rd
            }
            per_day.append(
                {
                    "trading_day": d.isoformat(),
                    "coverage": cov.coverage,
                    "largest_gap_min": cov.largest_gap_min,
                    "num_bins": cov.expected_count,
                    "bins_with_files": len(cov.files_by_bin),
                    "num_unique_expiries": len(day_tokens),
                    "required_expiries_present": sorted(present_required),
                    "required_expiries_missing": [rd.isoformat() for rd in required_dates if rd.isoformat() not in present_required],
                }
            )
        avg_cov = sum(daily[d].coverage for d in seq) / 5
        largest_gap = max(daily[d].largest_gap_min for d in seq)
        candidates.append({
            "days": [d.isoformat() for d in seq],
            "avg_coverage": avg_cov,
            "max_largest_gap_min": largest_gap,
            "per_day": per_day,
        })

    (out_dir / "candidates.json").write_text(json.dumps(candidates, indent=2))

    # Rank all windows to pick the most complete, even if none pass the filter
    def score_window(seq: List[date]) -> Tuple[int, float, int]:
        sum_present = sum(daily[d].present_count for d in seq)
        avg_cov = sum(daily[d].coverage for d in seq) / 5
        max_gap = max(daily[d].largest_gap_min for d in seq)
        return (sum_present, avg_cov, -max_gap)

    ranked = sorted(all_windows, key=score_window, reverse=True)
    top = ranked[:3]
    windows_summary = [
        {
            "days": [d.isoformat() for d in w],
            "sum_present": sum(daily[d].present_count for d in w),
            "avg_coverage": sum(daily[d].coverage for d in w) / 5,
            "max_largest_gap_min": max(daily[d].largest_gap_min for d in w),
            "per_day": [
                {
                    "trading_day": d.isoformat(),
                    "coverage": daily[d].coverage,
                    "present_count": daily[d].present_count,
                    "expected_count": daily[d].expected_count,
                    "largest_gap_min": daily[d].largest_gap_min,
                }
                for d in w
            ],
        }
        for w in all_windows
    ]
    (out_dir / "windows_all.json").write_text(json.dumps(windows_summary, indent=2))

    # Also emit CSV summary for quick viewing
    csv_lines = ["idx,days,sum_present,avg_coverage,max_largest_gap_min,per_day_coverage"]
    for idx, w in enumerate(all_windows, 1):
        days_str = "|".join(d.isoformat() for d in w)
        per_day_cov = "|".join(f"{daily[d].coverage:.3f}" for d in w)
        csv_lines.append(
            f"{idx},{days_str},{sum(daily[d].present_count for d in w)},{sum(daily[d].coverage for d in w)/5:.3f},{max(daily[d].largest_gap_min for d in w)},{per_day_cov}"
        )
    (out_dir / "windows_all.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    # Choose the best window
    chosen = ranked[0] if ranked else []
    if chosen:
        # Gaps per day
        gaps = {d.isoformat(): missing_intervals_for_day(daily[d]) for d in chosen}
        (out_dir / "chosen_window_gaps.json").write_text(json.dumps(gaps, indent=2))

        # Emit bins CSV for spreadsheet use
        bins_rows: List[str] = ["day,bin,present"]
        for d in chosen:
            cov = daily[d]
            bins, keys = expected_bins_for_day(cov)
            present = set(cov.files_by_bin.keys()) & keys
            for b in bins:
                k = b.strftime("%Y-%m-%d %H:%M")
                bins_rows.append(f"{d.isoformat()},{k},{1 if k in present else 0}")
        (out_dir / "chosen_window_bins.csv").write_text("\n".join(bins_rows))

        # Manifests (present and missing)
        present_paths: List[str] = []
        missing_bins_lines: List[str] = []
        for d in chosen:
            cov = daily[d]
            bins, keys = expected_bins_for_day(cov)
            present = set(cov.files_by_bin.keys()) & keys
            for b in bins:
                k = b.strftime("%Y-%m-%d %H:%M")
                if k in present:
                    present_paths.append(cov.files_by_bin[k])
                else:
                    missing_bins_lines.append(f"{d.isoformat()},{k}")
        (out_dir / "chosen_window_manifest.txt").write_text("\n".join(sorted(set(present_paths))), encoding="utf-8")
        (out_dir / "chosen_window_missing_bins.txt").write_text("\n".join(missing_bins_lines), encoding="utf-8")

        # Expiries per bin and per day
        cal_map = load_expiration_calendar_map(Path(args.calendar))
        per_day_tokens: Dict[str, Dict[str, int]] = {}
        expiries_by_bin: Dict[str, Dict[str, List[str]]] = {}
        for d in chosen:
            cov = daily[d]
            day_key = d.isoformat()
            per_day_tokens[day_key] = {}
            expiries_by_bin[day_key] = {}
            for bin_key, file_path in cov.files_by_bin.items():
                toks = sorted(read_expiries_from_csv(Path(file_path)))
                expiries_by_bin[day_key][bin_key] = toks
                for t in toks:
                    per_day_tokens[day_key][t] = per_day_tokens[day_key].get(t, 0) + 1

        resolved_by_day: Dict[str, Dict[str, int]] = {}
        for day_key, token_counts in per_day_tokens.items():
            resolved: Dict[str, int] = {}
            for t, n in token_counts.items():
                dt = token_to_date_guess(t, cal_map)
                if dt is not None:
                    resolved[dt.isoformat()] = resolved.get(dt.isoformat(), 0) + n
            resolved_by_day[day_key] = resolved
        (out_dir / "chosen_window_expiries.json").write_text(
            json.dumps({
                "per_day_tokens": per_day_tokens,
                "resolved_dates": resolved_by_day,
            }, indent=2)
        )

        # CSV: tokens per day
        exp_csv = ["day,token,count,resolved_date"]
        for day_key, token_counts in per_day_tokens.items():
            for t, n in sorted(token_counts.items()):
                dt = token_to_date_guess(t, cal_map)
                exp_csv.append(f"{day_key},{t},{n},{dt.isoformat() if dt else ''}")
        (out_dir / "chosen_window_expiries_by_day.csv").write_text("\n".join(exp_csv), encoding="utf-8")

        # Simple HTML visuals
        heatmap_html = [
            "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif} .row{display:flex; align-items:center; margin:4px 0} .cell{width:6px; height:12px; margin-right:1px;} .ok{background:#2ecc71} .miss{background:#e74c3c} .day{width:110px; font-weight:bold;}</style></head><body>",
            f"<h3>Chosen 5-day window: {' ,'.join(d.isoformat() for d in chosen)}</h3>",
        ]
        for d in chosen:
            cov = daily[d]
            bins, keys = expected_bins_for_day(cov)
            present = set(cov.files_by_bin.keys()) & keys
            row = [f"<div class='row'><div class='day'>{d.isoformat()}</div>"]
            for b in bins:
                k = b.strftime("%Y-%m-%d %H:%M")
                cls = "ok" if k in present else "miss"
                row.append(f"<div class='cell {cls}' title='{k}'></div>")
            row.append("</div>")
            heatmap_html.append("".join(row))
        heatmap_html.append("</body></html>")
        (out_dir / "gaps_by_day.html").write_text("\n".join(heatmap_html), encoding="utf-8")

        # Expiries per day HTML
        exp_html = [
            "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif} .day{margin:10px 0;padding:8px;border:1px solid #ddd;border-radius:6px} .tag{display:inline-block;margin:3px;padding:3px 6px;border-radius:4px;background:#eef} .hdr{font-weight:bold;margin-bottom:6px}</style></head><body>",
            f"<h3>Expiries per day for window: {' ,'.join(d.isoformat() for d in chosen)}</h3>",
        ]
        for d in chosen:
            day_key = d.isoformat()
            token_counts = per_day_tokens.get(day_key, {})
            resolved = resolved_by_day.get(day_key, {})
            exp_html.append(f"<div class='day'><div class='hdr'>{day_key} — tokens</div>")
            for t, n in sorted(token_counts.items()):
                exp_html.append(f"<span class='tag' title='count {n}'>{t} ({n})</span>")
            exp_html.append("<div class='hdr' style='margin-top:6px'>resolved dates</div>")
            for dt_str, n in sorted(resolved.items()):
                exp_html.append(f"<span class='tag' title='count {n}'>{dt_str} ({n})</span>")
            exp_html.append("</div>")
        exp_html.append("</body></html>")
        (out_dir / "expiries_by_day.html").write_text("\n".join(exp_html), encoding="utf-8")

        # Console summary
        print("Top windows (sum_present, avg_cov, max_gap):")
        for i, seq in enumerate(ranked[:3], 1):
            sum_present = sum(daily[d].present_count for d in seq)
            avg_cov = sum(daily[d].coverage for d in seq) / 5
            max_gap = max(daily[d].largest_gap_min for d in seq)
            print(i, sum_present, f"{avg_cov:.3f}", max_gap, "days:", ",".join(d.isoformat() for d in seq))
        print("Chosen window:", ",".join(d.isoformat() for d in chosen))

    print(f"Wrote per-day coverage to {out_dir/'coverage_by_day.json'}, candidates to {out_dir/'candidates.json'}, and window visuals under {out_dir}")


if __name__ == "__main__":
    main()


