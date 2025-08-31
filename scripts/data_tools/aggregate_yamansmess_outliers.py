from __future__ import annotations

import csv
from pathlib import Path


def aggregate() -> None:
    """Concatenate all *_outliers.csv files in the yamansmess folder into one CSV.

    - Writes header exactly once (deduplicate column headers only).
    - Assumes all input CSVs share identical column order and names.
    - Output file: lib/trading/bond_future_options/data_validation/yamansmess/yamansmess_outliers_aggregated.csv
    """

    repo_root = Path(__file__).resolve().parents[2]
    ym_dir = repo_root / "lib" / "trading" / "bond_future_options" / "data_validation" / "yamansmess"
    if not ym_dir.exists():
        raise SystemExit(f"Directory not found: {ym_dir}")

    input_files = sorted(p for p in ym_dir.glob("*outliers.csv") if p.is_file())
    if not input_files:
        raise SystemExit("No *outliers.csv files found to aggregate.")

    output_path = ym_dir / "yamansmess_outliers_aggregated.csv"

    rows_written = 0
    with output_path.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)

        # Use the first file as the canonical header
        first_file = input_files[0]
        with first_file.open("r", newline="", encoding="utf-8-sig") as f0:
            r0 = csv.reader(f0)
            try:
                header = next(r0)
            except StopIteration:
                raise SystemExit(f"First CSV is empty: {first_file}")
            writer.writerow(header)
            for row in r0:
                writer.writerow(row)
                rows_written += 1

        # Append remaining files, validating header equality and skipping their headers
        for fp in input_files[1:]:
            with fp.open("r", newline="", encoding="utf-8-sig") as f:
                r = csv.reader(f)
                try:
                    hdr = next(r)
                except StopIteration:
                    # Empty file; skip
                    continue
                if hdr != header:
                    raise SystemExit(
                        f"Header mismatch in {fp.name}. Expected {header}, found {hdr}."
                    )
                for row in r:
                    writer.writerow(row)
                    rows_written += 1

    print(
        f"Aggregated {len(input_files)} file(s) into {output_path} with {rows_written} row(s)."
    )


if __name__ == "__main__":
    aggregate()


