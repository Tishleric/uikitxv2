import csv
import math
from pathlib import Path
from typing import Optional

ADJTHEOR_THRESHOLD = 0.015625


def main() -> None:
    """Summarize Plex CSVs: total rows and |error_2nd_order|>5 counts."""
    repo_root = Path(__file__).resolve().parents[1]
    root = repo_root / "lib" / "trading" / "bond_future_options" / "data_validation" / "accuracy_validation"
    grand_total = grand_gt5 = grand_skipped = grand_csvs = 0
    # Success tracking over numeric error_2nd_order rows only
    grand_num = grand_success = 0
    grand_mneg_num = grand_mneg_success = 0
    grand_adj_num = grand_adj_success = 0
    grand_both_num = grand_both_success = 0
    # Collect rows for export:
    # - both conditions (moneyness<0 & adjtheor>threshold) AND finite |error_2nd_order|>5
    # - moneyness-only (moneyness<0) AND finite |error_2nd_order|>5 (adjtheor unrestricted)
    export_rows = []
    mneg_export_rows = []
    export_header = None
    for folder in sorted([d for d in root.iterdir() if d.is_dir() and d.name.endswith("Plex")], key=lambda p: p.name):
        folder_total = folder_gt5 = folder_skipped = folder_csvs = 0
        folder_num = folder_success = 0
        folder_mneg_num = folder_mneg_success = 0
        folder_adj_num = folder_adj_success = 0
        folder_both_num = folder_both_success = 0
        for csv_path in folder.glob("*.csv"):
            if not csv_path.name.endswith("_Plex.csv"):
                continue
            total = gt5 = skipped = 0
            with csv_path.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if export_header is None:
                    # Preserve original column order and add source columns at front
                    export_header = ["source_folder", "source_file"] + list(reader.fieldnames or [])
                for row in reader:
                    total += 1
                    try:
                        raw_val_obj = row.get("error_2nd_order")
                        raw_val_str: Optional[str] = None if raw_val_obj is None else str(raw_val_obj).strip()
                        v = float(raw_val_str if raw_val_str is not None else "")
                    except (ValueError, TypeError):
                        skipped += 1
                        continue
                    v_finite = math.isfinite(v)
                    if v_finite and abs(v) > 5:
                        gt5 += 1
                    # success metrics over numeric rows
                    if v_finite:
                        folder_num += 1
                    is_success = v_finite and abs(v) <= 5
                    if is_success:
                        folder_success += 1
                    # moneyness filter
                    try:
                        m_raw = row.get("moneyness")
                        m_str = None if m_raw is None else str(m_raw).strip()
                        m_val = float(m_str) if m_str else None
                    except (ValueError, TypeError):
                        m_val = None
                    if m_val is not None and m_val < 0:
                        folder_mneg_num += 1
                        if is_success:
                            folder_mneg_success += 1
                    # adjtheor filter
                    try:
                        a_raw = row.get("adjtheor")
                        a_str = None if a_raw is None else str(a_raw).strip()
                        a_val = float(a_str) if a_str else None
                    except (ValueError, TypeError):
                        a_val = None
                    if a_val is not None and a_val > ADJTHEOR_THRESHOLD:
                        folder_adj_num += 1
                        if is_success:
                            folder_adj_success += 1
                    # both filters
                    both_filters = (
                        m_val is not None and m_val < 0 and a_val is not None and a_val > ADJTHEOR_THRESHOLD
                    )
                    if both_filters:
                        folder_both_num += 1
                        if is_success:
                            folder_both_success += 1
                        if v_finite and abs(v) > 5:
                            # Export row
                            export_rows.append({
                                **{"source_folder": folder.name, "source_file": csv_path.name},
                                **row,
                            })
                    # moneyness-only export (includes adjtheor <= threshold), finite errors only
                    if m_val is not None and m_val < 0 and v_finite and abs(v) > 5:
                        mneg_export_rows.append({
                            **{"source_folder": folder.name, "source_file": csv_path.name},
                            **row,
                        })
            folder_total += total
            folder_gt5 += gt5
            folder_skipped += skipped
            folder_csvs += 1
        # aggregate to grand totals for success metrics
        grand_num += folder_num
        grand_success += folder_success
        grand_mneg_num += folder_mneg_num
        grand_mneg_success += folder_mneg_success
        grand_adj_num += folder_adj_num
        grand_adj_success += folder_adj_success
        grand_both_num += folder_both_num
        grand_both_success += folder_both_success

        err_pct = (folder_gt5 / folder_total * 100.0) if folder_total else 0.0
        succ_pct = (folder_success / folder_num * 100.0) if folder_num else 0.0
        mneg_pct = (folder_mneg_success / folder_mneg_num * 100.0) if folder_mneg_num else 0.0
        adj_pct = (folder_adj_success / folder_adj_num * 100.0) if folder_adj_num else 0.0
        both_pct = (folder_both_success / folder_both_num * 100.0) if folder_both_num else 0.0
        print(
            f"{folder.name}: files={folder_csvs} rows={folder_total} gt5={folder_gt5} "
            f"({err_pct:.2f}% error) skipped={folder_skipped} | "
            f"success_num={folder_success}/{folder_num} ({succ_pct:.2f}%)"
        )
        print(
            f"    moneyness<0: {folder_mneg_success}/{folder_mneg_num} ({mneg_pct:.2f}%), "
            f"adjtheor>{ADJTHEOR_THRESHOLD}: {folder_adj_success}/{folder_adj_num} ({adj_pct:.2f}%), "
            f"both: {folder_both_success}/{folder_both_num} ({both_pct:.2f}%)"
        )
        grand_total += folder_total
        grand_gt5 += folder_gt5
        grand_skipped += folder_skipped
        grand_csvs += folder_csvs
    overall_pct = (grand_gt5 / grand_total * 100.0) if grand_total else 0.0
    print("-" * 60)
    overall_succ_pct = (grand_success / grand_num * 100.0) if grand_num else 0.0
    overall_mneg_pct = (grand_mneg_success / grand_mneg_num * 100.0) if grand_mneg_num else 0.0
    overall_adj_pct = (grand_adj_success / grand_adj_num * 100.0) if grand_adj_num else 0.0
    overall_both_pct = (grand_both_success / grand_both_num * 100.0) if grand_both_num else 0.0
    print(
        f"ALL Plex: files={grand_csvs} rows={grand_total} gt5={grand_gt5} "
        f"({overall_pct:.2f}% error) skipped={grand_skipped} | "
        f"success_num={grand_success}/{grand_num} ({overall_succ_pct:.2f}%)"
    )
    print(
        f"    moneyness<0: {grand_mneg_success}/{grand_mneg_num} ({overall_mneg_pct:.2f}%), "
        f"adjtheor>{ADJTHEOR_THRESHOLD}: {grand_adj_success}/{grand_adj_num} ({overall_adj_pct:.2f}%), "
        f"both: {grand_both_success}/{grand_both_num} ({overall_both_pct:.2f}%)"
    )

    # Write export CSVs
    if export_rows:
        out_path = repo_root / "data" / "output" / "accuracy_validation"
        out_path.mkdir(parents=True, exist_ok=True)
        out_csv = out_path / "plex_both_gt5_errors.csv"
        # Ensure header includes all keys observed
        if export_header is None:
            export_header = ["source_folder", "source_file"]
        # Accumulate any new keys seen later
        for r in export_rows:
            for k in r.keys():
                if k not in export_header:
                    export_header.append(k)
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=export_header)
            writer.writeheader()
            for r in export_rows:
                writer.writerow(r)
        print(f"Exported {len(export_rows)} rows to {out_csv}")
    if mneg_export_rows:
        out_path2 = repo_root / "data" / "output" / "accuracy_validation"
        out_path2.mkdir(parents=True, exist_ok=True)
        out_csv2 = out_path2 / "plex_mneg_gt5_errors.csv"
        # Ensure header includes all keys observed
        header2 = list(export_header or ["source_folder", "source_file"])
        for r in mneg_export_rows:
            for k in r.keys():
                if k not in header2:
                    header2.append(k)
        with out_csv2.open("w", newline="", encoding="utf-8") as f2:
            writer2 = csv.DictWriter(f2, fieldnames=header2)
            writer2.writeheader()
            for r in mneg_export_rows:
                writer2.writerow(r)
        print(f"Exported {len(mneg_export_rows)} rows to {out_csv2}")


if __name__ == "__main__":
    main()


