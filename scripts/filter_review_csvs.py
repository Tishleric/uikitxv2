"""Filter review CSVs to keep:
- All rows with error == inf (case-insensitive), not counted in top-5.
- Top 5 rows with error <= 5 by greatest absolute moneyness.
- Top 5 rows with greatest (finite) error values.
Other rows are removed. Header is preserved; selected rows keep original order.

Usage: python scripts/filter_review_csvs.py <csv> [<csv> ...]
If no files are passed, it auto-discovers files under the review directory.
"""
from __future__ import annotations
import csv, math, sys, os, glob


def _to_float(s: str) -> float | None:
    t = (s or "").strip().lower()
    if t == "inf" or t == "+inf":
        return math.inf
    if t == "-inf":
        return -math.inf
    try:
        return float(t)
    except Exception:
        return None


def process_file(path: str) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return
    header = rows[0]
    try:
        idx_m = header.index("moneyness")
        idx_e = header.index("error")
    except ValueError:
        return
    body = rows[1:]
    finf, finite = [], []
    for i, r in enumerate(body):
        e = _to_float(r[idx_e])
        if e is None or math.isinf(e):
            finf.append(i)
            continue
        m = _to_float(r[idx_m])
        if m is None:
            continue
        finite.append((i, r, e, abs(m)))
    a = [i for i, _, e, am in sorted((x for x in finite if x[2] <= 5), key=lambda t: t[3], reverse=True)[:5]]
    b = [i for i, _, e, am in sorted(finite, key=lambda t: t[2], reverse=True)[:5]]
    keep_idx = set(finf) | set(a) | set(b)
    kept = [header] + [r for i, r in enumerate(body) if i in keep_idx]
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(kept)


def main() -> None:
    files = sys.argv[1:]
    if not files:
        pattern = os.path.join(
            "lib", "trading", "bond_future_options", "data_validation", "review", "*_pnl_diff.csv"
        )
        files = sorted(glob.glob(pattern))
    for p in files:
        process_file(p)


if __name__ == "__main__":
    main()


