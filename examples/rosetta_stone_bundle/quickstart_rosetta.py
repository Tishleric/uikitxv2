from rosetta_stone import RosettaStone


def main() -> None:
    rs = RosettaStone()
    # A couple of basic translations to verify the bundle works
    print(rs.translate("XCME.VY3.21JUL25.111:75.C", "actantrisk", "bloomberg"))
    print(rs.translate("VBYN25C3 111.75 Comdty", "bloomberg", "actantrisk"))


if __name__ == "__main__":
    main()

