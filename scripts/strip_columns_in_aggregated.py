#!/usr/bin/env python3
"""
Strip specified columns from all CSVs in
lib/trading/bond_future_options/generatedcsvs/aggregated/.

Columns to remove (case/format-insensitive):
  - implied vol
  - delta f
  - delta y (also handles 'detla y')
  - gamma f
  - gamma y
  - speed f (also handles 'speedf')
  - speed y
  - theta f
  - vega price
  - vega y
  - calc error

No other columns are touched; files are rewritten in place.
"""

from __future__ import annotations

from pathlib import Path
import csv
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
AGG_DIR = REPO_ROOT / "lib/trading/bond_future_options/generatedcsvs/aggregated"


def _normalize(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("_", " ")
    s = s.replace("-", " ")
    s = " ".join(s.split())  # collapse whitespace
    # common typos/variants
    s = s.replace("detla", "delta")
    s = s.replace("speedf", "speed f")
    s = s.replace("vega price", "vega price")
    s = s.replace("implied vol", "implied vol")
    s = s.replace("calc error", "calc error")
    return s


TARGETS = {
    "implied vol",
    "delta f",
    "delta y",
    "gamma f",
    "gamma y",
    "speed f",
    "speed y",
    "theta f",
    "vega price",
    "vega y",
    "calc error",
}


def strip_columns_in_file(path: Path) -> tuple[int, list[str]]:
    removed_cols: list[str] = []
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        try:
            header = next(reader)
        except StopIteration:
            return 0, removed_cols  # empty file

        # Decide which columns to drop by normalized name
        normalized = [_normalize(h) for h in header]
        drop_idx = [i for i, n in enumerate(normalized) if n in TARGETS]
        removed_cols = [header[i] for i in drop_idx]

        if not drop_idx:
            return 0, removed_cols

        keep_idx = [i for i in range(len(header)) if i not in drop_idx]

        with tmp_path.open("w", newline="", encoding="utf-8") as wf:
            writer = csv.writer(wf)
            writer.writerow([header[i] for i in keep_idx])
            for row in reader:
                # Guard against ragged rows
                if len(row) < len(header):
                    row = row + [""] * (len(header) - len(row))
                writer.writerow([row[i] for i in keep_idx])

    # Replace original file atomically
    tmp_path.replace(path)
    return len(removed_cols), removed_cols


def main() -> None:
    if not AGG_DIR.exists():
        print(f"Aggregated directory not found: {AGG_DIR}")
        sys.exit(1)

    csv_files = sorted(AGG_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found to process.")
        return

    total_removed = 0
    for f in csv_files:
        removed_count, removed_cols = strip_columns_in_file(f)
        if removed_count:
            total_removed += removed_count
            print(f"Stripped {removed_count} columns from {f.name}: {', '.join(removed_cols)}")
        else:
            print(f"No target columns found in {f.name}")

    print(f"Done. Files processed: {len(csv_files)}. Columns removed (per file sum): {total_removed}")


if __name__ == "__main__":
    main()


