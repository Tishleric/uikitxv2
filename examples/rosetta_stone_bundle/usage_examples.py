from rosetta_stone import RosettaStone


def show(title: str, value: str) -> None:
    print(f"{title}: {value}")


def demo_matrix() -> None:
    rs = RosettaStone()

    formats = [
        "bloomberg",
        "cme",
        "actantrisk",
        "actanttrades",
        "actanttime",
        "broker",
    ]

    # Sample symbols per format (options)
    samples_options = {
        "actantrisk": "XCME.VY3.21JUL25.111:75.C",
        "bloomberg": "VBYN25C3 111.75 Comdty",
        "cme": "VY3N5 C11100",
        "actanttrades": "XCMEOCADPS20250728N0VY4/111.75",
        "actanttime": "XCME.ZN.N.G.21JUL25",
        "broker": "CALL JUL 25 CBT 10YR TNOTE 111.75",
    }

    # Sample symbols per format (futures)
    samples_futures = {
        "actantrisk": "XCME.ZN.SEP25",
        "bloomberg": "TYU5 Comdty",
        "actanttrades": "XCMEFFDPSX20250919U0ZN",
        "broker": "SEP 25 CBT 10YR TNOTE",
    }

    print("\n=== Option translations (pairwise) ===")
    for src_fmt, src_symbol in samples_options.items():
        for dst_fmt in formats:
            if src_fmt == dst_fmt:
                continue
            result = rs.translate(src_symbol, src_fmt, dst_fmt)
            show(f"{src_fmt} -> {dst_fmt}", str(result))

    print("\n=== Futures translations (pairwise) ===")
    for src_fmt, src_symbol in samples_futures.items():
        for dst_fmt in formats:
            if src_fmt == dst_fmt:
                continue
            result = rs.translate(src_symbol, src_fmt, dst_fmt)
            show(f"{src_fmt} -> {dst_fmt}", str(result))


def main() -> None:
    demo_matrix()


if __name__ == "__main__":
    main()

