import argparse
from pathlib import Path

from rosetta_stone import RosettaStone


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate symbols across formats using RosettaStone")
    parser.add_argument("--from", dest="from_fmt", required=True, help="Source format: bloomberg|cme|actantrisk|actanttrades|actanttime|broker")
    parser.add_argument("--to", dest="to_fmt", required=True, help="Target format")
    parser.add_argument("--symbol", dest="symbol", required=True, help="Input symbol string")
    parser.add_argument("--csv", dest="csv_path", default=None, help="Optional CSV path (defaults to bundled CSV)")

    args = parser.parse_args()

    if args.csv_path:
        rs = RosettaStone(csv_path=Path(args.csv_path))
    else:
        rs = RosettaStone()

    translated = rs.translate(args.symbol, args.from_fmt, args.to_fmt)
    print(translated)


if __name__ == "__main__":
    main()

