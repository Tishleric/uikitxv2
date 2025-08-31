from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

SENTINEL = "-2146826259"


def strip_file(path: Path) -> Dict[str, int]:
    tmp = path.with_suffix(path.suffix + ".tmp")
    removed = 0
    kept = 0
    with path.open("r", encoding="utf-8") as rfh, tmp.open("w", encoding="utf-8") as wfh:
        for i, line in enumerate(rfh):
            if i == 0:
                wfh.write(line)
                continue
            if SENTINEL in line:
                removed += 1
                continue
            wfh.write(line)
            kept += 1
    path.unlink()
    tmp.rename(path)
    return {"removed": removed, "kept": kept}


def main() -> None:
    ap = argparse.ArgumentParser(description="Hard-strip any line containing -2146826259 from by-instrument CSVs (in place)")
    ap.add_argument("--root", default="data/FiveMinuteMarketSelected_by_instrument")
    args = ap.parse_args()

    root = Path(args.root)
    totals = {"files": 0, "removed": 0, "kept": 0}
    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir():
            continue
        for f in sorted(exp_dir.glob("*.csv")):
            res = strip_file(f)
            totals["files"] += 1
            totals["removed"] += res["removed"]
            totals["kept"] += res["kept"]
    (root / "hard_strip_summary.json").write_text(json.dumps(totals, indent=2), encoding="utf-8")
    print(totals)


if __name__ == "__main__":
    main()



