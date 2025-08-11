#!/usr/bin/env python
"""
Translate a list of Bloomberg symbols to ActantRisk using RosettaStone.
- Input: one symbol per line (default: bbgsymbolstotranslate.md)
- Output: CSV at data/output/symbol_translations/bbg_to_actantrisk.csv
"""

import argparse
import csv
from pathlib import Path

from lib.trading.market_prices.rosetta_stone import RosettaStone


def normalize_bbg(line: str) -> str:
    """Normalize a raw line into a Bloomberg symbol string RosettaStone can parse.
    Ensures at least two tokens by appending 'Comdty' for futures-like inputs.
    """
    s = line.strip().strip('"').strip("'")
    if not s or s.startswith(('#', '//')):
        return ""
    if "Comdty" in s:
        left = s.split("Comdty", 1)[0].strip()
        return f"{left} Comdty" if left else ""
    parts = s.split()
    if len(parts) == 1:
        return f"{s} Comdty"
    return s


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate Bloomberg symbols to ActantRisk")
    parser.add_argument("--input", default="bbgsymbolstotranslate.md", help="Path to input file")
    parser.add_argument(
        "--output",
        default="data/output/symbol_translations/bbg_to_actantrisk.csv",
        help="Path to output CSV",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rs = RosettaStone()
    with in_path.open("r", encoding="utf-8") as f, out_path.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["line_no", "raw", "normalized_bbg", "actantrisk", "status", "error"])
        for i, raw in enumerate(f, start=1):
            norm = normalize_bbg(raw)
            if not norm:
                continue
            try:
                translated = rs.translate(norm, "bloomberg", "actantrisk")
                status = "ok" if translated else "not_found"
                writer.writerow([i, raw.strip(), norm, translated or "", status, ""])
            except Exception as e:  # noqa: BLE001
                writer.writerow([i, raw.strip(), norm, "", "error", str(e)])


if __name__ == "__main__":
    main()